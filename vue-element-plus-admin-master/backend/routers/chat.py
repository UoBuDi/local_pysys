"""
在线聊天路由
包含发送消息、聊天历史、标记已读、会话列表、文件上传等接口
房间ID命名规范（符合文档9.10节）：
  - 大厅: lobby
  - 私聊: chat_{min_uid}_{max_uid}
  - 群聊: group_{group_id}

CH-01: 搜索 / CH-02: 群聊管理 / CH-03: 撤回 / CH-04: 图片消息
CH-05: 已读回执 / CH-06: 导出 / CH-07: 置顶免打扰 / CH-08: @提及
"""

import json
import logging
import os
import uuid
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import PlainTextResponse
from typing import Optional, List

from core.dependencies import get_current_user
from core.config import get_config as get_app_config
from core.ws_manager_instance import status_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# 图片扩展名白名单
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}


# ==================== CH-01: 搜索消息 ====================

@router.get("/api/chat/search/")
async def search_messages(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    room_id: Optional[str] = Query(None, description="限定房间ID，不传则搜全部"),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user)
):
    """搜索聊天消息（CH-01）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 只搜索用户所在房间的消息
                if room_id:
                    cursor.execute(
                        "SELECT id, room_id, sender_id, sender_name, content_type, content, "
                        "is_recalled, created_at FROM chat_messages "
                        "WHERE room_id = %s AND content LIKE %s AND is_recalled = 0 "
                        "ORDER BY created_at DESC LIMIT %s",
                        (room_id, f"%{keyword}%", limit)
                    )
                else:
                    cursor.execute(
                        "SELECT m.id, m.room_id, m.sender_id, m.sender_name, m.content_type, m.content, "
                        "m.is_recalled, m.created_at FROM chat_messages m "
                        "INNER JOIN chat_sessions cs ON cs.room_id = m.room_id AND cs.user_id = %s "
                        "WHERE m.content LIKE %s AND m.is_recalled = 0 "
                        "ORDER BY m.created_at DESC LIMIT %s",
                        (user_id, f"%{keyword}%", limit)
                    )
                rows = cursor.fetchall()
                results = [
                    {
                        "id": row[0],
                        "room_id": row[1],
                        "sender_id": row[2],
                        "sender_name": row[3],
                        "content_type": row[4],
                        "content": row[5],
                        "is_recalled": row[6],
                        "created_at": row[7].isoformat() if row[7] else None
                    }
                    for row in rows
                ]
                return {"code": 200, "data": results}
    except Exception as e:
        logger.error(f"搜索消息失败: {e}")
        return {"code": 500, "message": "搜索消息失败"}


# ==================== 发送消息（含 CH-08 @提及） ====================

@router.post("/api/chat/send/")
async def send_message(
    room_id: str = Query(..., description="房间ID"),
    content_type: str = Query("text", description="消息类型: text/file/image"),
    content: str = Query(..., description="消息内容"),
    mentioned_user_ids: str = Query(None, description="@提及用户ID列表，逗号分隔"),
    user: dict = Depends(get_current_user)
):
    """发送聊天消息（含 CH-08 @提及支持）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")
        sender_avatar = ""

        # 解析 @提及用户ID
        mention_ids = None
        if mentioned_user_ids:
            try:
                mention_ids = json.dumps([int(x) for x in mentioned_user_ids.split(",") if x.strip()])
            except ValueError:
                mention_ids = None

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT avatar FROM users WHERE id = %s", (user_id,))
                av_row = cursor.fetchone()
                if av_row and av_row[0]:
                    sender_avatar = av_row[0]

                cursor.execute(
                    "INSERT INTO chat_messages "
                    "(room_id, sender_id, sender_name, content_type, content, mentioned_user_ids) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (room_id, user_id, username, content_type, content, mention_ids)
                )
                message_id = cursor.lastrowid

                cursor.execute(
                    "UPDATE chat_sessions SET last_message_id = %s, updated_at = NOW() WHERE room_id = %s",
                    (message_id, room_id)
                )
                cursor.execute(
                    "UPDATE chat_sessions SET unread_count = unread_count + 1 "
                    "WHERE room_id = %s AND user_id != %s",
                    (room_id, user_id)
                )
                cursor.execute(
                    "INSERT IGNORE INTO chat_sessions (user_id, room_id, last_message_id, unread_count) "
                    "VALUES (%s, %s, %s, 0)",
                    (user_id, room_id, message_id)
                )
                conn.commit()

        # 构建广播数据
        broadcast_data = {
            "id": message_id,
            "room_id": room_id,
            "sender_id": user_id,
            "sender_name": username,
            "sender_avatar": sender_avatar,
            "content_type": content_type,
            "content": content,
            "mentioned_user_ids": json.loads(mention_ids) if mention_ids else [],
            "created_at": datetime.now().isoformat()
        }

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_message",
                data=broadcast_data,
                from_user_id=user_id,
                room_id=room_id
            )
        )

        # CH-08: 被@用户单独推送提醒
        if mention_ids:
            mentioned = json.loads(mention_ids)
            for uid in mentioned:
                await status_manager.send_to_user(
                    uid,
                    status_manager.build_message(
                        msg_type="chat_mentioned",
                        data=broadcast_data,
                        from_user_id=user_id
                    )
                )

        return {"code": 200, "data": broadcast_data}
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return {"code": 500, "message": "发送消息失败"}


# ==================== 获取聊天历史 ====================

@router.get("/api/chat/history/{room_id}")
async def get_chat_history(
    room_id: str,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = Query(None, description="加载此ID之前的消息"),
    user: dict = Depends(get_current_user)
):
    """获取聊天历史记录"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                if before_id:
                    cursor.execute(
                        "SELECT id, room_id, sender_id, sender_name, content_type, content, "
                        "is_recalled, mentioned_user_ids, file_name, created_at "
                        "FROM chat_messages WHERE room_id = %s AND id < %s "
                        "ORDER BY id DESC LIMIT %s",
                        (room_id, before_id, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT id, room_id, sender_id, sender_name, content_type, content, "
                        "is_recalled, mentioned_user_ids, file_name, created_at "
                        "FROM chat_messages WHERE room_id = %s "
                        "ORDER BY id DESC LIMIT %s",
                        (room_id, limit)
                    )
                rows = cursor.fetchall()
                messages = [
                    {
                        "id": row[0],
                        "room_id": row[1],
                        "sender_id": row[2],
                        "sender_name": row[3],
                        "content_type": row[4],
                        "content": row[5],
                        "is_recalled": row[6] or 0,
                        "mentioned_user_ids": json.loads(row[7]) if row[7] else [],
                        "file_name": row[8],
                        "created_at": row[9].isoformat() if row[9] else None
                    }
                    for row in reversed(rows)
                ]
                return {"code": 200, "data": messages}
    except Exception as e:
        logger.error(f"获取聊天历史失败: {e}")
        return {"code": 500, "message": "获取聊天历史失败"}


# ==================== 标记已读（含 CH-05 已读回执） ====================

@router.post("/api/chat/read/{room_id}")
async def mark_room_read(
    room_id: str,
    user: dict = Depends(get_current_user)
):
    """标记房间消息已读（清零unread_count + CH-05 写入已读记录）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 清零未读计数
                cursor.execute(
                    "UPDATE chat_sessions SET unread_count = 0 "
                    "WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )
                # CH-05: 批量写入已读记录（该房间所有未读消息标记为已读）
                cursor.execute(
                    "INSERT IGNORE INTO chat_message_read (message_id, user_id) "
                    "SELECT id, %s FROM chat_messages "
                    "WHERE room_id = %s AND sender_id != %s AND is_recalled = 0",
                    (user_id, room_id, user_id)
                )
                conn.commit()
        return {"code": 200, "data": {"room_id": room_id, "unread_count": 0}}
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return {"code": 500, "message": "标记已读失败"}


# ==================== CH-05: 消息已读回执 ====================

@router.get("/api/chat/read-status/{room_id}")
async def get_read_status(
    room_id: str,
    message_id: Optional[int] = Query(None, description="指定消息ID，不传则返回最近一条"),
    user: dict = Depends(get_current_user)
):
    """获取消息已读状态（CH-05）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 获取房间成员数
                if room_id.startswith("group_"):
                    cursor.execute(
                        "SELECT COUNT(*) FROM chat_sessions WHERE room_id = %s",
                        (room_id,)
                    )
                    member_count = cursor.fetchone()[0]
                else:
                    member_count = 2  # 私聊固定2人

                # 获取目标消息
                if message_id:
                    target_id = message_id
                else:
                    cursor.execute(
                        "SELECT id FROM chat_messages WHERE room_id = %s AND is_recalled = 0 "
                        "ORDER BY id DESC LIMIT 1",
                        (room_id,)
                    )
                    row = cursor.fetchone()
                    if not row:
                        return {"code": 200, "data": {"read_count": 0, "total_count": member_count, "readers": []}}
                    target_id = row[0]

                # 查询已读人数
                cursor.execute(
                    "SELECT cmr.user_id, u.username FROM chat_message_read cmr "
                    "LEFT JOIN users u ON cmr.user_id = u.id "
                    "WHERE cmr.message_id = %s",
                    (target_id,)
                )
                readers = [{"user_id": r[0], "username": r[1]} for r in cursor.fetchall()]

                return {
                    "code": 200,
                    "data": {
                        "message_id": target_id,
                        "read_count": len(readers),
                        "total_count": member_count,
                        "readers": readers
                    }
                }
    except Exception as e:
        logger.error(f"获取已读状态失败: {e}")
        return {"code": 500, "message": "获取已读状态失败"}


# ==================== 会话列表（含 CH-07 置顶/免打扰） ====================

@router.get("/api/chat/sessions/")
async def get_chat_sessions(
    user: dict = Depends(get_current_user)
):
    """获取当前用户的会话列表（自动加入大厅，含 CH-07 置顶/免打扰）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 确保用户已加入大厅
                cursor.execute(
                    "SELECT room_id FROM chat_sessions WHERE user_id = %s AND room_id = 'lobby'",
                    (user_id,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                        "VALUES (%s, 'lobby', '大厅', 'group')",
                        (user_id,)
                    )
                    conn.commit()

                cursor.execute(
                    "SELECT cs.room_id, cs.room_name, cs.room_type, cs.unread_count, "
                    "cs.last_message_id, cs.updated_at, cs.is_pinned, cs.is_muted, "
                    "cm.content AS last_content, cm.content_type AS last_content_type, "
                    "cm.sender_name AS last_sender_name, cm.created_at AS last_created_at "
                    "FROM chat_sessions cs "
                    "LEFT JOIN chat_messages cm ON cs.last_message_id = cm.id "
                    "WHERE cs.user_id = %s "
                    "ORDER BY cs.is_pinned DESC, "
                    "CASE WHEN cs.room_id = 'lobby' THEN 0 ELSE 1 END, "
                    "cs.updated_at DESC",
                    (user_id,)
                )
                rows = cursor.fetchall()

                # 批量查询私聊对方头像
                avatar_map = {}
                for row in rows:
                    room_id = row[0]
                    room_type = row[2]
                    if room_type == 'private' and room_id.startswith('chat_'):
                        parts = room_id.replace('chat_', '').split('_')
                        other_uid = next((int(p) for p in parts if int(p) != user_id), None)
                        if other_uid and other_uid not in avatar_map:
                            cursor.execute("SELECT avatar FROM users WHERE id = %s", (other_uid,))
                            av_row = cursor.fetchone()
                            avatar_map[other_uid] = av_row[0] if av_row and av_row[0] else ""

                sessions = []
                for row in rows:
                    session = {
                        "room_id": row[0],
                        "room_name": row[1],
                        "room_type": row[2],
                        "unread_count": row[3],
                        "last_message_id": row[4],
                        "updated_at": row[5].isoformat() if row[5] else None,
                        "is_pinned": row[6] or 0,
                        "is_muted": row[7] or 0,
                        "last_content": row[8],
                        "last_content_type": row[9],
                        "last_sender_name": row[10],
                        "last_created_at": row[11].isoformat() if row[11] else None,
                        "avatar": ""
                    }
                    if row[2] == 'private' and row[0].startswith('chat_'):
                        parts = row[0].replace('chat_', '').split('_')
                        other_uid = next((int(p) for p in parts if int(p) != user_id), 0)
                        session["avatar"] = avatar_map.get(other_uid, "")
                    sessions.append(session)

                return {"code": 200, "data": sessions}
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return {"code": 500, "message": "获取会话列表失败"}


# ==================== CH-07: 会话置顶/免打扰 ====================

@router.put("/api/chat/session-settings/")
async def update_session_settings(
    room_id: str = Query(..., description="房间ID"),
    is_pinned: Optional[int] = Query(None, description="置顶: 0/1"),
    is_muted: Optional[int] = Query(None, description="免打扰: 0/1"),
    user: dict = Depends(get_current_user)
):
    """更新会话设置（CH-07 置顶/免打扰）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        updates = []
        params = []
        if is_pinned is not None:
            updates.append("is_pinned = %s")
            params.append(is_pinned)
        if is_muted is not None:
            updates.append("is_muted = %s")
            params.append(is_muted)

        if not updates:
            return {"code": 400, "message": "未指定更新项"}

        params.extend([room_id, user_id])
        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"UPDATE chat_sessions SET {', '.join(updates)} WHERE room_id = %s AND user_id = %s",
                    tuple(params)
                )
                conn.commit()

        return {"code": 200, "data": {"room_id": room_id, "is_pinned": is_pinned, "is_muted": is_muted}}
    except Exception as e:
        logger.error(f"更新会话设置失败: {e}")
        return {"code": 500, "message": "更新会话设置失败"}


# ==================== CH-02: 群聊创建与管理 ====================

@router.post("/api/chat/create-room/")
async def create_chat_room(
    target_user_id: int = Query(..., description="对方用户ID"),
    room_type: str = Query("private", description="房间类型: private/group"),
    room_name: str = Query(None, description="房间名称（群聊必填）"),
    member_ids: str = Query(None, description="群聊成员ID列表，逗号分隔"),
    user: dict = Depends(get_current_user)
):
    """创建聊天房间（私聊或群聊，CH-02 群聊支持多成员）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")

        if room_type == "private":
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT cs1.room_id FROM chat_sessions cs1 "
                        "JOIN chat_sessions cs2 ON cs1.room_id = cs2.room_id "
                        "WHERE cs1.user_id = %s AND cs2.user_id = %s AND cs1.room_type = 'private'",
                        (user_id, target_user_id)
                    )
                    existing = cursor.fetchone()
                    if existing:
                        return {"code": 200, "data": {"room_id": existing[0], "is_new": False}}

                    room_id = f"chat_{min(user_id, target_user_id)}_{max(user_id, target_user_id)}"
                    cursor.execute("SELECT username FROM users WHERE id = %s", (target_user_id,))
                    target_row = cursor.fetchone()
                    target_name = target_row[0] if target_row else f"用户{target_user_id}"

                    cursor.execute(
                        "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                        "VALUES (%s, %s, %s, 'private')",
                        (user_id, room_id, target_name)
                    )
                    cursor.execute(
                        "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                        "VALUES (%s, %s, %s, 'private')",
                        (target_user_id, room_id, username)
                    )
                    conn.commit()

            await status_manager.broadcast_to_room(
                room_id,
                status_manager.build_message(
                    msg_type="chat_room_created",
                    data={"room_id": room_id, "room_name": username, "room_type": "private", "created_by": username},
                    from_user_id=user_id
                )
            )
            return {"code": 200, "data": {"room_id": room_id, "is_new": True}}
        else:
            # 群聊：支持多成员
            room_id = f"group_{uuid.uuid4().hex[:12]}"
            display_name = room_name or "群聊"

            # 解析成员列表
            all_member_ids = [user_id]
            if member_ids:
                try:
                    all_member_ids.extend([int(x) for x in member_ids.split(",") if x.strip()])
                except ValueError:
                    pass
            if target_user_id not in all_member_ids:
                all_member_ids.append(target_user_id)
            all_member_ids = list(set(all_member_ids))  # 去重

            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    # 为每个成员创建会话记录
                    for uid in all_member_ids:
                        cursor.execute(
                            "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                            "VALUES (%s, %s, %s, 'group')",
                            (uid, room_id, display_name)
                        )
                    # 写入群成员表，创建者为 owner
                    for uid in all_member_ids:
                        role = "owner" if uid == user_id else "member"
                        cursor.execute(
                            "INSERT IGNORE INTO chat_group_members (room_id, user_id, role) "
                            "VALUES (%s, %s, %s)",
                            (room_id, uid, role)
                        )
                    conn.commit()

            # 通知所有成员
            await status_manager.broadcast_to_room(
                room_id,
                status_manager.build_message(
                    msg_type="chat_room_created",
                    data={"room_id": room_id, "room_name": display_name, "room_type": "group", "created_by": username},
                    from_user_id=user_id
                )
            )
            return {"code": 200, "data": {"room_id": room_id, "is_new": True}}
    except Exception as e:
        logger.error(f"创建聊天房间失败: {e}")
        return {"code": 500, "message": "创建聊天房间失败"}


@router.get("/api/chat/group-members/{room_id}")
async def get_group_members(
    room_id: str,
    user: dict = Depends(get_current_user)
):
    """获取群聊成员列表（CH-02）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT gm.user_id, gm.role, gm.joined_at, u.username, u.avatar "
                    "FROM chat_group_members gm "
                    "LEFT JOIN users u ON gm.user_id = u.id "
                    "WHERE gm.room_id = %s ORDER BY gm.role = 'owner' DESC, gm.joined_at",
                    (room_id,)
                )
                rows = cursor.fetchall()
                members = [
                    {
                        "user_id": row[0],
                        "role": row[1],
                        "joined_at": row[2].isoformat() if row[2] else None,
                        "username": row[3] or "",
                        "avatar": row[4] or ""
                    }
                    for row in rows
                ]
                return {"code": 200, "data": members}
    except Exception as e:
        logger.error(f"获取群成员失败: {e}")
        return {"code": 500, "message": "获取群成员失败"}


@router.post("/api/chat/add-group-members/")
async def add_group_members(
    room_id: str = Query(..., description="群聊房间ID"),
    member_ids: str = Query(..., description="新增成员ID列表，逗号分隔"),
    user: dict = Depends(get_current_user)
):
    """添加群聊成员（CH-02）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        new_ids = [int(x) for x in member_ids.split(",") if x.strip()]

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 验证操作者是群成员
                cursor.execute(
                    "SELECT role FROM chat_group_members WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )
                op_row = cursor.fetchone()
                if not op_row:
                    return {"code": 403, "message": "非群成员无法操作"}

                # 获取群名称
                cursor.execute("SELECT room_name FROM chat_sessions WHERE room_id = %s LIMIT 1", (room_id,))
                name_row = cursor.fetchone()
                group_name = name_row[0] if name_row else "群聊"

                for uid in new_ids:
                    cursor.execute(
                        "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                        "VALUES (%s, %s, %s, 'group')",
                        (uid, room_id, group_name)
                    )
                    cursor.execute(
                        "INSERT IGNORE INTO chat_group_members (room_id, user_id, role) "
                        "VALUES (%s, %s, 'member')",
                        (room_id, uid)
                    )
                conn.commit()

        return {"code": 200, "data": {"room_id": room_id, "added_count": len(new_ids)}}
    except Exception as e:
        logger.error(f"添加群成员失败: {e}")
        return {"code": 500, "message": "添加群成员失败"}


@router.put("/api/chat/group-name/")
async def update_group_name(
    room_id: str = Query(..., description="群聊房间ID"),
    room_name: str = Query(..., description="新群名称"),
    user: dict = Depends(get_current_user)
):
    """修改群名称（CH-02）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 验证操作者是群主或管理员
                cursor.execute(
                    "SELECT role FROM chat_group_members WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )
                op_row = cursor.fetchone()
                if not op_row or op_row[0] not in ("owner", "admin"):
                    return {"code": 403, "message": "仅群主或管理员可修改群名称"}

                cursor.execute(
                    "UPDATE chat_sessions SET room_name = %s WHERE room_id = %s",
                    (room_name, room_id)
                )
                conn.commit()

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_group_renamed",
                data={"room_id": room_id, "room_name": room_name},
                from_user_id=user_id,
                room_id=room_id
            )
        )
        return {"code": 200, "data": {"room_id": room_id, "room_name": room_name}}
    except Exception as e:
        logger.error(f"修改群名称失败: {e}")
        return {"code": 500, "message": "修改群名称失败"}


@router.post("/api/chat/leave-group/{room_id}")
async def leave_group(
    room_id: str,
    user: dict = Depends(get_current_user)
):
    """退出群聊（CH-02）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM chat_group_members WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )
                cursor.execute(
                    "DELETE FROM chat_sessions WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )
                conn.commit()

        return {"code": 200, "data": {"room_id": room_id}}
    except Exception as e:
        logger.error(f"退出群聊失败: {e}")
        return {"code": 500, "message": "退出群聊失败"}


# ==================== CH-03: 消息撤回 ====================

@router.post("/api/chat/recall/{message_id}")
async def recall_message(
    message_id: int,
    user: dict = Depends(get_current_user)
):
    """撤回消息（2分钟内，CH-03）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT sender_id, room_id, created_at FROM chat_messages WHERE id = %s",
                    (message_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return {"code": 404, "message": "消息不存在"}
                if row[0] != user_id:
                    return {"code": 403, "message": "只能撤回自己的消息"}

                # 2分钟限制
                elapsed = (datetime.now() - row[2]).total_seconds()
                if elapsed > 120:
                    return {"code": 400, "message": "消息已超过2分钟，无法撤回"}

                room_id = row[1]
                cursor.execute(
                    "UPDATE chat_messages SET is_recalled = 1 WHERE id = %s",
                    (message_id,)
                )
                conn.commit()

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_message_recalled",
                data={"id": message_id, "room_id": room_id, "recalled_by": user_id},
                from_user_id=user_id,
                room_id=room_id
            )
        )
        return {"code": 200, "data": {"id": message_id}}
    except Exception as e:
        logger.error(f"撤回消息失败: {e}")
        return {"code": 500, "message": "撤回消息失败"}


# ==================== CH-04: 图片上传 ====================

@router.post("/api/chat/upload-image/")
async def upload_chat_image(
    file: UploadFile = File(...),
    room_id: str = Query(..., description="房间ID"),
    user: dict = Depends(get_current_user)
):
    """上传聊天图片（CH-04），自动识别图片类型"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")

        # 校验文件扩展名
        file_ext = os.path.splitext(file.filename or "image")[1].lower()
        if file_ext not in IMAGE_EXTENSIONS:
            return {"code": 400, "message": f"不支持的图片格式: {file_ext}"}

        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat_images")
        os.makedirs(upload_dir, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, stored_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        file_url = f"/static/chat_images/{stored_name}"

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chat_messages "
                    "(room_id, sender_id, sender_name, content_type, content, file_name) "
                    "VALUES (%s, %s, %s, 'image', %s, %s)",
                    (room_id, user_id, username, file_url, file.filename)
                )
                message_id = cursor.lastrowid

                cursor.execute(
                    "UPDATE chat_sessions SET last_message_id = %s, updated_at = NOW() WHERE room_id = %s",
                    (message_id, room_id)
                )
                cursor.execute(
                    "UPDATE chat_sessions SET unread_count = unread_count + 1 "
                    "WHERE room_id = %s AND user_id != %s",
                    (room_id, user_id)
                )
                conn.commit()

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_message",
                data={
                    "id": message_id,
                    "room_id": room_id,
                    "sender_id": user_id,
                    "sender_name": username,
                    "sender_avatar": "",
                    "content_type": "image",
                    "content": file_url,
                    "file_name": file.filename,
                    "created_at": datetime.now().isoformat()
                },
                from_user_id=user_id,
                room_id=room_id
            )
        )

        return {"code": 200, "data": {"id": message_id, "file_url": file_url, "file_name": file.filename}}
    except Exception as e:
        logger.error(f"上传图片失败: {e}")
        return {"code": 500, "message": "上传图片失败"}


# ==================== 在线用户 ====================

@router.get("/api/chat/online-users/")
async def get_online_users(
    user: dict = Depends(get_current_user)
):
    """获取在线用户列表（基于WebSocket连接状态）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        online_user_ids = set()
        for conn_info in status_manager.frontend_connections:
            uid = conn_info.get("user_id")
            if uid:
                online_user_ids.add(uid)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, avatar FROM users WHERE id != %s AND status = 1 ORDER BY username",
                    (user_id,)
                )
                rows = cursor.fetchall()
                users = [
                    {"id": row[0], "username": row[1], "avatar": row[2] or "", "online": row[0] in online_user_ids}
                    for row in rows
                ]
        return {"code": 200, "data": users}
    except Exception as e:
        logger.error(f"获取在线用户失败: {e}")
        return {"code": 500, "message": "获取在线用户失败"}


# ==================== 文件上传 ====================

@router.post("/api/chat/upload/")
async def upload_chat_file(
    file: UploadFile = File(...),
    room_id: str = Query(..., description="房间ID"),
    user: dict = Depends(get_current_user)
):
    """上传聊天文件"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")

        # CH-04: 自动识别图片类型
        file_ext = os.path.splitext(file.filename or "file")[1].lower()
        is_image = file_ext in IMAGE_EXTENSIONS

        if is_image:
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat_images")
            content_type = "image"
        else:
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat_files")
            content_type = "file"

        os.makedirs(upload_dir, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, stored_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        file_url = f"/static/chat_images/{stored_name}" if is_image else f"/static/chat_files/{stored_name}"

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chat_messages "
                    "(room_id, sender_id, sender_name, content_type, content, file_name) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (room_id, user_id, username, content_type, file_url, file.filename)
                )
                message_id = cursor.lastrowid

                cursor.execute(
                    "UPDATE chat_sessions SET last_message_id = %s, updated_at = NOW() WHERE room_id = %s",
                    (message_id, room_id)
                )
                cursor.execute(
                    "UPDATE chat_sessions SET unread_count = unread_count + 1 "
                    "WHERE room_id = %s AND user_id != %s",
                    (room_id, user_id)
                )
                conn.commit()

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_message",
                data={
                    "id": message_id,
                    "room_id": room_id,
                    "sender_id": user_id,
                    "sender_name": username,
                    "sender_avatar": "",
                    "content_type": content_type,
                    "content": file_url,
                    "file_name": file.filename,
                    "created_at": datetime.now().isoformat()
                },
                from_user_id=user_id,
                room_id=room_id
            )
        )

        return {"code": 200, "data": {"id": message_id, "file_url": file_url, "file_name": file.filename}}
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return {"code": 500, "message": "上传文件失败"}


# ==================== CH-06: 聊天记录导出 ====================

@router.get("/api/chat/export/{room_id}")
async def export_chat_history(
    room_id: str,
    format: str = Query("text", description="导出格式: text/html"),
    user: dict = Depends(get_current_user)
):
    """导出聊天记录（CH-06）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                # 获取房间名称
                cursor.execute(
                    "SELECT room_name FROM chat_sessions WHERE room_id = %s AND user_id = %s LIMIT 1",
                    (room_id, user.get("id", 0))
                )
                name_row = cursor.fetchone()
                if not name_row:
                    return {"code": 403, "message": "无权导出此会话"}
                room_name = name_row[0] or room_id

                cursor.execute(
                    "SELECT sender_name, content_type, content, is_recalled, created_at "
                    "FROM chat_messages WHERE room_id = %s ORDER BY created_at ASC",
                    (room_id,)
                )
                rows = cursor.fetchall()

        if format == "html":
            lines = [
                "<!DOCTYPE html><html><head><meta charset='utf-8'>",
                f"<title>{room_name} - 聊天记录</title>",
                "<style>body{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px}",
                ".msg{padding:8px 0;border-bottom:1px solid #eee}",
                ".time{color:#999;font-size:12px}.name{font-weight:bold}.recalled{color:#999;font-style:italic}",
                "img{max-width:300px;border-radius:4px}</style></head><body>",
                f"<h2>{room_name} - 聊天记录</h2>"
            ]
            for row in rows:
                sender, ctype, content, recalled, created = row
                time_str = created.strftime("%Y-%m-%d %H:%M:%S") if created else ""
                if recalled:
                    lines.append(f'<div class="msg"><span class="time">{time_str}</span> <span class="name">{sender}</span> <span class="recalled">[已撤回]</span></div>')
                elif ctype == "image":
                    lines.append(f'<div class="msg"><span class="time">{time_str}</span> <span class="name">{sender}</span> <img src="{content}"></div>')
                elif ctype == "file":
                    lines.append(f'<div class="msg"><span class="time">{time_str}</span> <span class="name">{sender}</span> <a href="{content}">[文件]</a></div>')
                else:
                    lines.append(f'<div class="msg"><span class="time">{time_str}</span> <span class="name">{sender}</span> {content}</div>')
            lines.append("</body></html>")
            return PlainTextResponse("\n".join(lines), media_type="text/html; charset=utf-8")
        else:
            # 纯文本格式
            lines = [f"{room_name} - 聊天记录", "=" * 40]
            for row in rows:
                sender, ctype, content, recalled, created = row
                time_str = created.strftime("%Y-%m-%d %H:%M:%S") if created else ""
                if recalled:
                    lines.append(f"[{time_str}] {sender}: [已撤回]")
                elif ctype == "image":
                    lines.append(f"[{time_str}] {sender}: [图片] {content}")
                elif ctype == "file":
                    lines.append(f"[{time_str}] {sender}: [文件] {content}")
                else:
                    lines.append(f"[{time_str}] {sender}: {content}")
            return PlainTextResponse("\n".join(lines), media_type="text/plain; charset=utf-8")
    except Exception as e:
        logger.error(f"导出聊天记录失败: {e}")
        return {"code": 500, "message": "导出聊天记录失败"}


# ==================== 删除消息 ====================

@router.delete("/api/chat/message/{message_id}")
async def delete_message(
    message_id: int,
    user: dict = Depends(get_current_user)
):
    """删除聊天消息（仅发送者可删除）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT sender_id, room_id FROM chat_messages WHERE id = %s",
                    (message_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return {"code": 404, "message": "消息不存在"}
                if row[0] != user_id:
                    return {"code": 403, "message": "无权删除此消息"}

                room_id = row[1]
                cursor.execute(
                    "DELETE FROM chat_message_read WHERE message_id = %s",
                    (message_id,)
                )
                cursor.execute(
                    "DELETE FROM chat_messages WHERE id = %s AND sender_id = %s",
                    (message_id, user_id)
                )
                conn.commit()

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_message_deleted",
                data={"id": message_id, "room_id": room_id},
                from_user_id=user_id,
                room_id=room_id
            )
        )
        return {"code": 200, "data": {"id": message_id}}
    except Exception as e:
        logger.error(f"删除消息失败: {e}")
        return {"code": 500, "message": "删除消息失败"}
