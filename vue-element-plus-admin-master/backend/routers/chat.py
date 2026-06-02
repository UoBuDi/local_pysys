"""
在线聊天路由
包含发送消息、聊天历史、标记已读、会话列表、文件上传等接口
房间ID命名规范（符合文档9.10节）：
  - 大厅: lobby
  - 私聊: chat_{min_uid}_{max_uid}
  - 群聊: group_{group_id}
"""

import logging
import os
import uuid
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, Query, UploadFile, File
from typing import Optional

from core.dependencies import get_current_user
from core.config import get_config as get_app_config
from core.ws_manager_instance import status_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/chat/send/")
async def send_message(
    room_id: str = Query(..., description="房间ID"),
    content_type: str = Query("text", description="消息类型: text/file"),
    content: str = Query(..., description="消息内容"),
    user: dict = Depends(get_current_user)
):
    """发送聊天消息"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")
        sender_avatar = ""

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT avatar FROM users WHERE id = %s",
                    (user_id,)
                )
                av_row = cursor.fetchone()
                if av_row and av_row[0]:
                    sender_avatar = av_row[0]

                cursor.execute(
                    "INSERT INTO chat_messages (room_id, sender_id, sender_name, content_type, content) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (room_id, user_id, username, content_type, content)
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

        await status_manager.broadcast_to_room(
            room_id,
            status_manager.build_message(
                msg_type="chat_message",
                data={
                    "id": message_id,
                    "room_id": room_id,
                    "sender_id": user_id,
                    "sender_name": username,
                    "sender_avatar": sender_avatar,
                    "content_type": content_type,
                    "content": content,
                    "created_at": datetime.now().isoformat()
                },
                from_user_id=user_id,
                room_id=room_id
            )
        )

        return {
            "code": 200,
            "data": {
                "id": message_id,
                "room_id": room_id,
                "sender_id": user_id,
                "sender_name": username,
                "content_type": content_type,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return {"code": 500, "message": "发送消息失败"}


@router.get("/api/chat/history/{room_id}")
async def get_chat_history(
    room_id: str,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = Query(None, description="加载此ID之前的消息（向上翻页）"),
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
                        "SELECT id, room_id, sender_id, sender_name, content_type, content, created_at "
                        "FROM chat_messages WHERE room_id = %s AND id < %s "
                        "ORDER BY id DESC LIMIT %s",
                        (room_id, before_id, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT id, room_id, sender_id, sender_name, content_type, content, created_at "
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
                        "created_at": row[6].isoformat() if row[6] else None
                    }
                    for row in reversed(rows)
                ]
                return {"code": 200, "data": messages}
    except Exception as e:
        logger.error(f"获取聊天历史失败: {e}")
        return {"code": 500, "message": "获取聊天历史失败"}


@router.post("/api/chat/read/{room_id}")
async def mark_room_read(
    room_id: str,
    user: dict = Depends(get_current_user)
):
    """标记房间消息已读（清零unread_count）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE chat_sessions SET unread_count = 0 "
                    "WHERE room_id = %s AND user_id = %s",
                    (room_id, user_id)
                )
                conn.commit()
        return {"code": 200, "data": {"room_id": room_id, "unread_count": 0}}
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return {"code": 500, "message": "标记已读失败"}


@router.get("/api/chat/sessions/")
async def get_chat_sessions(
    user: dict = Depends(get_current_user)
):
    """获取当前用户的会话列表（自动加入大厅）"""
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
                    "cs.last_message_id, cs.updated_at, "
                    "cm.content AS last_content, cm.content_type AS last_content_type, "
                    "cm.sender_name AS last_sender_name, cm.created_at AS last_created_at "
                    "FROM chat_sessions cs "
                    "LEFT JOIN chat_messages cm ON cs.last_message_id = cm.id "
                    "WHERE cs.user_id = %s "
                    "ORDER BY "
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
                        other_uid = None
                        for p in parts:
                            if int(p) != user_id:
                                other_uid = int(p)
                                break
                        if other_uid and other_uid not in avatar_map:
                            cursor.execute(
                                "SELECT avatar FROM users WHERE id = %s",
                                (other_uid,)
                            )
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
                        "last_content": row[6],
                        "last_content_type": row[7],
                        "last_sender_name": row[8],
                        "last_created_at": row[9].isoformat() if row[9] else None,
                        "avatar": ""
                    }
                    # 私聊房间填充对方头像
                    if row[2] == 'private' and row[0].startswith('chat_'):
                        parts = row[0].replace('chat_', '').split('_')
                        other_uid = next((int(p) for p in parts if int(p) != user_id), 0)
                        session["avatar"] = avatar_map.get(other_uid, "")
                    sessions.append(session)

                return {"code": 200, "data": sessions}
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return {"code": 500, "message": "获取会话列表失败"}


@router.post("/api/chat/create-room/")
async def create_chat_room(
    target_user_id: int = Query(..., description="对方用户ID"),
    room_type: str = Query("private", description="房间类型: private/group"),
    room_name: str = Query(None, description="房间名称（群聊必填）"),
    user: dict = Depends(get_current_user)
):
    """创建聊天房间（私聊或群聊）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")

        if room_type == "private":
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    # 查找两个用户共同的私聊房间
                    cursor.execute(
                        "SELECT cs1.room_id FROM chat_sessions cs1 "
                        "JOIN chat_sessions cs2 ON cs1.room_id = cs2.room_id "
                        "WHERE cs1.user_id = %s AND cs2.user_id = %s "
                        "AND cs1.room_type = 'private'",
                        (user_id, target_user_id)
                    )
                    existing = cursor.fetchone()
                    if existing:
                        return {"code": 200, "data": {"room_id": existing[0], "is_new": False}}

                    # 文档9.10规范：私聊房间ID格式 chat_{min_uid}_{max_uid}
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
                f"chat_{min(user_id, target_user_id)}_{max(user_id, target_user_id)}",
                status_manager.build_message(
                    msg_type="chat_room_created",
                    data={
                        "room_id": room_id,
                        "room_name": username,
                        "room_type": "private",
                        "created_by": username
                    },
                    from_user_id=user_id
                )
            )

            return {"code": 200, "data": {"room_id": room_id, "is_new": True}}
        else:
            # 群聊
            room_id = f"group_{uuid.uuid4().hex[:12]}"
            display_name = room_name or "群聊"

            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                        "VALUES (%s, %s, %s, 'group')",
                        (user_id, room_id, display_name)
                    )
                    cursor.execute(
                        "INSERT IGNORE INTO chat_sessions (user_id, room_id, room_name, room_type) "
                        "VALUES (%s, %s, %s, 'group')",
                        (target_user_id, room_id, display_name)
                    )
                    conn.commit()

            return {"code": 200, "data": {"room_id": room_id, "is_new": True}}
    except Exception as e:
        logger.error(f"创建聊天房间失败: {e}")
        return {"code": 500, "message": "创建聊天房间失败"}


@router.get("/api/chat/online-users/")
async def get_online_users(
    user: dict = Depends(get_current_user)
):
    """获取在线用户列表（基于WebSocket连接状态）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        user_id = user.get("id", 0)

        # 从WebSocket管理器获取在线用户ID集合
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
                    {
                        "id": row[0],
                        "username": row[1],
                        "avatar": row[2] or "",
                        "online": row[0] in online_user_ids
                    }
                    for row in rows
                ]

        return {"code": 200, "data": users}
    except Exception as e:
        logger.error(f"获取在线用户失败: {e}")
        return {"code": 500, "message": "获取在线用户失败"}


@router.post("/api/chat/upload/")
async def upload_chat_file(
    file: UploadFile = File(...),
    room_id: str = Query(..., description="房间ID"),
    user: dict = Depends(get_current_user)
):
    """上传聊天文件"""
    try:
        config = get_app_config()
        user_id = user.get("id", 0)
        username = user.get("username", "unknown")

        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat_files")
        os.makedirs(upload_dir, exist_ok=True)

        file_ext = os.path.splitext(file.filename or "file")[1]
        file_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, file_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        file_url = f"/static/chat_files/{file_name}"

        from database import get_db_connection
        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chat_messages (room_id, sender_id, sender_name, content_type, content) "
                    "VALUES (%s, %s, %s, 'file', %s)",
                    (room_id, user_id, username, file_url)
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
                    "content_type": "file",
                    "content": file_url,
                    "file_name": file.filename,
                    "created_at": datetime.now().isoformat()
                },
                from_user_id=user_id,
                room_id=room_id
            )
        )

        return {
            "code": 200,
            "data": {
                "id": message_id,
                "file_url": file_url,
                "file_name": file.filename
            }
        }
    except Exception as e:
        logger.error(f"上传聊天文件失败: {e}")
        return {"code": 500, "message": "上传文件失败"}


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
