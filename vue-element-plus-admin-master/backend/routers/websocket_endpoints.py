"""
WebSocket 端点路由
包含状态同步、同步进度、日志推送等 WebSocket 接口以及相关 REST API
支持房间管理（join_room/leave_room）和协作事件（collab_event）
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional

from core.dependencies import get_current_user
from core.websocket_manager import ConnectionManager
from core.ws_manager_instance import status_manager
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局连接管理器实例
log_manager = ConnectionManager()
sync_progress_manager = ConnectionManager()


@router.websocket("/ws/status/{client_type}/{client_id}")
async def websocket_status(websocket: WebSocket, client_type: str, client_id: str,
                           token: Optional[str] = Query(None)):
    """状态同步 WebSocket 端点（前后端/GUI 通信，支持Token鉴权绑定用户身份）"""
    if client_type not in ["frontend", "gui"]:
        await websocket.close(code=4000, reason="Invalid client type")
        return

    # 前端连接时解析Token绑定用户身份
    user_id = None
    username = None
    if client_type == "frontend" and token:
        try:
            from core.security import decode_token
            payload = decode_token(token)
            if payload:
                username = payload.get("sub")
                if username:
                    try:
                        config = get_app_config()
                        from database import get_db_connection
                        with get_db_connection("USER_DB", config) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    "SELECT id FROM users WHERE username = %s",
                                    (username,)
                                )
                                row = cursor.fetchone()
                                if row:
                                    user_id = row[0]
                    except Exception as db_err:
                        logger.warning(f"WebSocket查询用户ID失败: {db_err}")
        except Exception as e:
            logger.warning(f"WebSocket Token解析失败: {e}")

    if client_type == "frontend":
        await status_manager.connect_frontend(websocket, client_id,
                                               user_id=user_id, username=username)
    else:
        await status_manager.connect_gui(websocket, client_id)

    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "data": {
                "clientType": client_type,
                "clientId": client_id,
                "timestamp": datetime.now().isoformat()
            }
        }))

        status = status_manager.get_status()
        await status_manager.broadcast_all(json.dumps({
            "type": "client_joined",
            "data": {
                "clientType": client_type,
                "clientId": client_id,
                "status": status
            }
        }))

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                if message.get("type") == "heartbeat":
                    await status_manager.update_heartbeat(websocket, client_type)
                    await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif message.get("type") == "get_status":
                    status = status_manager.get_status()
                    await websocket.send_text(json.dumps({
                        "type": "status_response",
                        "data": status
                    }))

                elif message.get("type") == "join_room":
                    room_id = message.get("roomId") or message.get("data", {}).get("roomId")
                    user_info = message.get("data", {}).get("userInfo", {})
                    if room_id:
                        await status_manager.join_room(client_id, room_id, user_info)
                        await websocket.send_text(json.dumps({
                            "type": "room_joined",
                            "data": {"roomId": room_id, "members": status_manager.get_room_members(room_id)}
                        }))
                        await status_manager.broadcast_to_room(room_id, {
                            "type": "member_joined",
                            "data": {"clientId": client_id, "userInfo": user_info},
                            "roomId": room_id
                        })

                elif message.get("type") == "leave_room":
                    room_id = message.get("roomId") or message.get("data", {}).get("roomId")
                    if room_id:
                        await status_manager.leave_room(client_id, room_id)
                        await status_manager.broadcast_to_room(room_id, {
                            "type": "member_left",
                            "data": {"clientId": client_id},
                            "roomId": room_id
                        })
                        await websocket.send_text(json.dumps({
                            "type": "room_left",
                            "data": {"roomId": room_id}
                        }))

                elif message.get("type") == "collab_event":
                    room_id = message.get("roomId") or message.get("data", {}).get("roomId")
                    event_data = message.get("data", {})
                    if room_id:
                        await status_manager.broadcast_to_room(room_id, {
                            "type": message.get("type"),
                            "fromUserId": message.get("fromUserId"),
                            "roomId": room_id,
                            "data": event_data,
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        })

                else:
                    await status_manager.broadcast_all(json.dumps({
                        "type": "message",
                        "data": {
                            "clientType": client_type,
                            "clientId": client_id,
                            "message": message
                        }
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        if client_type == "frontend":
            await status_manager.disconnect_frontend(websocket)
        else:
            await status_manager.disconnect_gui(websocket)

        status = status_manager.get_status()
        await status_manager.broadcast_all(json.dumps({
            "type": "client_left",
            "data": {
                "clientType": client_type,
                "clientId": client_id,
                "status": status
            }
        }))


@router.websocket("/ws/sync-progress/")
async def websocket_sync_progress(websocket: WebSocket):
    """同步进度 WebSocket 端点"""
    await sync_progress_manager.connect(websocket)

    try:
        from sync_manager import sync_manager

        current_status = await sync_manager.get_status()
        await websocket.send_text(json.dumps({
            "type": "progress",
            "data": current_status
        }))

        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        sync_progress_manager.disconnect(websocket)


@router.websocket("/ws/logs/")
async def websocket_logs(websocket: WebSocket):
    """日志推送 WebSocket 端点"""
    await log_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "subscribe":
                    log_type = message.get("log_type", "all")
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "data": {"logType": log_type}
                    }))

                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        log_manager.disconnect(websocket)


# ==================== WebSocket 相关 REST API ====================

@router.get("/api/ws/status")
async def get_ws_status(user: dict = Depends(get_current_user)):
    """获取当前 WebSocket 连接状态"""
    try:
        status = status_manager.get_status()

        return {
            "code": 200,
            "message": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取 WebSocket 状态失败: {e}")
        return {"code": 500, "message": "获取 WebSocket 状态失败"}


@router.get("/api/ws/stats")
async def get_ws_stats(user: dict = Depends(get_current_user)):
    """获取 WebSocket 统计信息"""
    try:
        stats_data = {}

        try:
            from websocket_stats import ws_stats
            stats_data = ws_stats.get_current_stats()
        except Exception as e:
            logger.warning(f"获取 WebSocket 统计模块失败: {e}")
            stats_data = {
                "totalConnections": len(status_manager.frontend_connections) +
                                  len(status_manager.gui_connections),
                "frontendConnections": len(status_manager.frontend_connections),
                "guiConnections": len(status_manager.gui_connections),
                "activeConnections": len(log_manager.active_connections) +
                                   len(sync_progress_manager.active_connections),
                "uptime": "unknown"
            }

        return {
            "code": 200,
            "message": "success",
            "data": stats_data
        }
    except Exception as e:
        logger.error(f"获取 WebSocket 统计失败: {e}")
        return {"code": 500, "message": "获取 WebSocket 统计失败"}


@router.get("/api/ws/stats/history")
async def get_ws_stats_history(
    hours: int = Query(24, ge=1, le=168),
    user: dict = Depends(get_current_user)
):
    """获取 WebSocket 历史统计（按小时聚合）"""
    try:
        history_data = []

        try:
            from websocket_stats import ws_stats
            history_data = ws_stats.get_hourly_history(hours=hours)
        except Exception as e:
            logger.warning(f"获取历史统计模块失败: {e}")
            for i in range(hours):
                history_data.append({
                    "hour": i,
                    "connections": 0,
                    "messages": 0,
                    "disconnections": 0
                })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "history": history_data,
                "periodHours": hours
            }
        }
    except Exception as e:
        logger.error(f"获取 WebSocket 历史统计失败: {e}")
        return {"code": 500, "message": "获取 WebSocket 历史统计失败"}
