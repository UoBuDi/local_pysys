"""
系统实时通知与管控路由
提供全站广播通知、定向推送、踢出用户、强制刷新权限等能力
通知为即发即弃模式，通过 WebSocket 实时推送到前端
"""

import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.config import get_config as get_app_config
from core.dependencies import get_current_user
from core.ws_manager_instance import status_manager
from database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 请求模型 ====================

class BroadcastRequest(BaseModel):
    """全站广播通知请求"""
    type: str = Field("system", description="通知类型: system/approval/alert")
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: Optional[str] = Field(None, description="通知内容")


class SendToUsersRequest(BaseModel):
    """定向推送通知请求"""
    type: str = Field("system", description="通知类型: system/approval/alert")
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: Optional[str] = Field(None, description="通知内容")
    target_user_ids: List[int] = Field(..., min_length=1, description="目标用户ID列表")


class KickUserRequest(BaseModel):
    """踢出用户请求"""
    user_id: int = Field(..., description="被踢出的用户ID")
    reason: Optional[str] = Field(None, description="踢出原因")


class ForceRefreshRequest(BaseModel):
    """强制刷新请求"""
    target_type: str = Field("all", description="刷新目标: all/user")
    target_user_ids: Optional[List[int]] = Field(None, description="指定用户ID列表（target_type=user时必填）")


# ==================== API 端点 ====================

@router.post("/api/notifications/broadcast")
async def broadcast_notification(request: BroadcastRequest, user: dict = Depends(get_current_user)):
    """全站广播通知

    向所有在线前端客户端推送系统通知，同时持久化到数据库。
    """
    try:
        config = get_app_config()
        sender_id = user.get("id")
        username = user.get("username", "系统")

        # 持久化通知到数据库
        notification_id = None
        try:
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO notifications (type, title, content, sender_id, target_type) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (request.type, request.title, request.content, sender_id, "all")
                    )
                    notification_id = cursor.lastrowid
                    conn.commit()
        except Exception as db_err:
            logger.warning(f"通知持久化失败（不影响推送）: {db_err}")

        # 通过 WebSocket 广播给所有前端客户端
        await status_manager.broadcast_to_frontend(
            status_manager.build_message(
                msg_type="system_notification",
                data={
                    "id": notification_id,
                    "type": request.type,
                    "title": request.title,
                    "content": request.content,
                    "sender": username,
                    "target_type": "all"
                }
            )
        )

        logger.info(f"全站广播通知: title={request.title} sender={username}")
        return {"code": 200, "message": "广播通知已发送"}

    except Exception as e:
        logger.error(f"广播通知失败: {e}")
        return {"code": 500, "message": f"广播通知失败: {str(e)}"}


@router.post("/api/notifications/send")
async def send_notification_to_users(request: SendToUsersRequest, user: dict = Depends(get_current_user)):
    """向指定用户推送通知

    仅向目标用户在线的 WebSocket 连接推送通知。
    """
    try:
        config = get_app_config()
        sender_id = user.get("id")
        username = user.get("username", "系统")

        # 持久化通知
        notification_id = None
        try:
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO notifications (type, title, content, sender_id, target_type, target_ids) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (request.type, request.title, request.content, sender_id,
                         "user", json.dumps(request.target_user_ids))
                    )
                    notification_id = cursor.lastrowid
                    conn.commit()
        except Exception as db_err:
            logger.warning(f"通知持久化失败（不影响推送）: {db_err}")

        # 向目标用户在线连接推送
        message = status_manager.build_message(
            msg_type="system_notification",
            data={
                "id": notification_id,
                "type": request.type,
                "title": request.title,
                "content": request.content,
                "sender": username,
                "target_type": "user",
                "target_user_ids": request.target_user_ids
            }
        )
        msg_str = json.dumps(message, ensure_ascii=False)

        sent_count = 0
        for conn_info in status_manager.frontend_connections:
            if conn_info.get("user_id") in request.target_user_ids:
                try:
                    await conn_info["websocket"].send_text(msg_str)
                    sent_count += 1
                except Exception:
                    continue

        logger.info(f"定向推送通知: title={request.title} targets={request.target_user_ids} sent={sent_count}")
        return {"code": 200, "message": f"通知已发送，在线送达 {sent_count} 人"}

    except Exception as e:
        logger.error(f"定向推送通知失败: {e}")
        return {"code": 500, "message": f"推送通知失败: {str(e)}"}


@router.post("/api/notifications/kick-user")
async def kick_user(request: KickUserRequest, user: dict = Depends(get_current_user)):
    """踢出指定在线用户

    向目标用户的 WebSocket 连接发送 kick_user 事件，
    前端收到后断开连接并跳转登录页。
    """
    try:
        operator = user.get("username", "管理员")

        # 向目标用户发送踢出事件
        message = status_manager.build_message(
            msg_type="kick_user",
            data={
                "user_id": request.user_id,
                "reason": request.reason or "您已被管理员踢出",
                "operator": operator
            }
        )
        msg_str = json.dumps(message, ensure_ascii=False)

        kicked_count = 0
        connections_to_kick = []
        for conn_info in status_manager.frontend_connections:
            if conn_info.get("user_id") == request.user_id:
                connections_to_kick.append(conn_info)

        for conn_info in connections_to_kick:
            try:
                await conn_info["websocket"].send_text(msg_str)
                # 发送后短暂延迟再关闭连接，确保客户端收到消息
                kicked_count += 1
            except Exception:
                continue

        # 延迟关闭连接（在后台任务中执行）
        if connections_to_kick:
            import asyncio
            async def close_kicked_connections():
                await asyncio.sleep(1)
                for conn_info in connections_to_kick:
                    try:
                        await conn_info["websocket"].close(code=4003, reason="Kicked by admin")
                    except Exception:
                        pass
            asyncio.create_task(close_kicked_connections())

        logger.info(f"踢出用户: user_id={request.user_id} reason={request.reason} operator={operator} kicked={kicked_count}")
        return {"code": 200, "message": f"已踢出用户，影响 {kicked_count} 个连接"}

    except Exception as e:
        logger.error(f"踢出用户失败: {e}")
        return {"code": 500, "message": f"踢出用户失败: {str(e)}"}


@router.post("/api/notifications/force-refresh")
async def force_refresh(request: ForceRefreshRequest, user: dict = Depends(get_current_user)):
    """强制前端刷新权限和菜单

    管理员修改了用户角色/权限后，通过此接口通知前端重新获取权限和菜单。
    """
    try:
        operator = user.get("username", "管理员")

        message = status_manager.build_message(
            msg_type="force_refresh",
            data={
                "operator": operator,
                "target_type": request.target_type,
                "target_user_ids": request.target_user_ids
            }
        )

        if request.target_type == "all":
            # 全站强制刷新
            await status_manager.broadcast_to_frontend(message)
            logger.info(f"全站强制刷新: operator={operator}")
            return {"code": 200, "message": "全站强制刷新指令已发送"}
        else:
            # 指定用户强制刷新
            msg_str = json.dumps(message, ensure_ascii=False)
            sent_count = 0
            for conn_info in status_manager.frontend_connections:
                if request.target_user_ids and conn_info.get("user_id") in request.target_user_ids:
                    try:
                        await conn_info["websocket"].send_text(msg_str)
                        sent_count += 1
                    except Exception:
                        continue
            logger.info(f"定向强制刷新: targets={request.target_user_ids} sent={sent_count}")
            return {"code": 200, "message": f"强制刷新指令已发送，在线送达 {sent_count} 人"}

    except Exception as e:
        logger.error(f"强制刷新失败: {e}")
        return {"code": 500, "message": f"强制刷新失败: {str(e)}"}


@router.get("/api/notifications/history")
async def get_notification_history(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user)
):
    """查询通知历史记录（分页）"""
    try:
        config = get_app_config()
        offset = (page - 1) * page_size

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as total FROM notifications")
                total = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT id, type, title, content, sender_id, target_type, target_ids, created_at "
                    "FROM notifications ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (page_size, offset)
                )
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                records = [dict(zip(columns, row)) for row in rows]

                # 序列化 JSON 字段和日期
                for record in records:
                    if record.get("target_ids") and isinstance(record["target_ids"], str):
                        try:
                            record["target_ids"] = json.loads(record["target_ids"])
                        except Exception:
                            pass
                    if record.get("created_at"):
                        record["created_at"] = str(record["created_at"])

        return {
            "code": 200,
            "message": "success",
            "data": {
                "records": records,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    except Exception as e:
        logger.error(f"查询通知历史失败: {e}")
        return {"code": 500, "message": f"查询失败: {str(e)}"}
