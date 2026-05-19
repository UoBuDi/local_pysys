"""
认证相关路由
包含登录、注册、登出、令牌刷新和验证等接口
"""

import logging
import hashlib

import pymysql
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    check_refresh_rate_limit,
    get_token_expires_at,
    get_refresh_token_expires_at
)
from core.dependencies import security, verify_token
from core.models import LoginCredentials, RegisterCredentials, RefreshTokenRequest
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/login/")
async def login(credentials: LoginCredentials):
    """用户登录验证"""
    config = get_app_config()
    
    try:
        from database import get_db_connection
        
        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT id, username, password FROM users WHERE username = %s"
                cursor.execute(sql, (credentials.username,))
                user = cursor.fetchone()

                if not user:
                    return {"code": 401, "message": "用户名或密码错误"}

                provided = credentials.password.encode('utf-8')
                stored = user['password']
                md5_hash = hashlib.md5(provided).hexdigest()
                if md5_hash != stored:
                    return {"code": 401, "message": "用户名或密码错误"}

                cursor.execute("""
                    SELECT r.id, r.name, r.code 
                    FROM roles r 
                    JOIN user_roles ur ON r.id = ur.role_id 
                    WHERE ur.user_id = %s AND r.status = 1
                """, (user['id'],))
                roles = cursor.fetchall()

                role_list = [role['name'] for role in roles] if roles else []

                access_token = create_access_token(data={"sub": user['username']})
                refresh_token = create_refresh_token(data={"sub": user['username']})

                return {
                    "code": 200,
                    "message": "登录成功",
                    "data": {
                        "user": {
                            "id": user['id'],
                            "username": user['username'],
                            "roles": roles if roles else [],
                            "roleList": role_list
                        },
                        "token": access_token,
                        "refreshToken": refresh_token,
                        "tokenType": "bearer",
                        "expiresAt": get_token_expires_at(),
                        "refreshExpiresAt": get_refresh_token_expires_at()
                    }
                }
            
    except Exception as e:
        logger.error(f"登录验证失败：{e}")
        return {"code": 500, "message": "登录验证失败"}


@router.post("/api/register/")
async def register(credentials: RegisterCredentials):
    """用户注册（使用事务保护）"""
    logger.info(f"开始处理注册请求: username={credentials.username}")
    config = get_app_config()

    if not credentials.username:
        return {"code": 400, "message": "用户名不能为空"}
    if not credentials.password:
        return {"code": 400, "message": "密码不能为空"}
    if len(credentials.password) < 6:
        return {"code": 400, "message": "密码长度不能少于6位"}

    try:
        from database import get_db_connection, transaction

        with get_db_connection("USER_DB", config) as conn:
            with transaction(conn):
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute("SELECT id, username FROM users WHERE username = %s", (credentials.username,))
                    existing_user = cursor.fetchone()

                    if existing_user:
                        raise ValueError("USER_EXISTS")

                    hashed_password = hash_password(credentials.password)

                    cursor.execute(
                        "INSERT INTO users (username, password, email, status, created_at) VALUES (%s, %s, %s, %s, NOW())",
                        (credentials.username, hashed_password, credentials.email or None, 1)
                    )

                    new_user_id = cursor.lastrowid
                    logger.info(f"用户注册成功: {credentials.username} (ID: {new_user_id})")

                    return {
                        "code": 200,
                        "message": "注册成功",
                        "data": {
                            "user": {
                                "id": new_user_id,
                                "username": credentials.username
                            }
                        }
                    }

    except ValueError as ve:
        if str(ve) == "USER_EXISTS":
            return {"code": 400, "message": "用户名已存在"}
        raise
    except pymysql.err.IntegrityError as e:
        logger.error(f"数据库完整性错误: {e}", exc_info=True)
        return {"code": 500, "message": "注册失败，数据完整性错误"}
    except pymysql.err.OperationalError as e:
        logger.error(f"数据库连接错误: {e}", exc_info=True)
        return {"code": 500, "message": "注册失败，无法连接到数据库"}
    except Exception as e:
        logger.error(f"用户注册异常: {e}", exc_info=True)
        return {"code": 500, "message": "注册失败，请稍后重试"}


@router.get("/api/user/loginOut")
async def login_out():
    """用户登出"""
    return {
        "code": 200,
        "message": "success"
    }


@router.post("/api/token/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """使用 Refresh Token 获取新的 Access Token"""
    config = get_app_config()

    try:
        payload = decode_token(request.refresh_token)

        if not payload:
            return {"code": 401, "message": "刷新令牌已过期或无效"}

        token_type = payload.get("type")
        if token_type != "refresh":
            return {"code": 401, "message": "无效的刷新令牌类型"}

        username = payload.get("sub")
        if not username:
            return {"code": 401, "message": "无效的刷新令牌"}

        allowed, message = check_refresh_rate_limit(username)
        if not allowed:
            return {"code": 429, "message": message}

        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT id, username, status FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()

                if not user:
                    return {"code": 401, "message": "用户不存在"}

                if user['status'] != 1:
                    return {"code": 401, "message": "用户已被禁用"}

                new_access_token = create_access_token(data={"sub": username})
                new_refresh_token = create_refresh_token(data={"sub": username})

                return {
                    "code": 200,
                    "message": "刷新成功",
                    "data": {
                        "token": new_access_token,
                        "refreshToken": new_refresh_token,
                        "tokenType": "bearer",
                        "expiresAt": get_token_expires_at(),
                        "refreshExpiresAt": get_refresh_token_expires_at()
                    }
                }

    except Exception as e:
        logger.error(f"刷新令牌失败: {e}")
        return {"code": 500, "message": "刷新令牌失败"}


@router.post("/api/token/validate")
async def validate_token(request: RefreshTokenRequest):
    """验证 Token 是否有效"""
    try:
        payload = decode_token(request.refresh_token)

        if not payload:
            return {
                "code": 401,
                "message": "令牌已过期或无效",
                "data": {"valid": False}
            }

        username = payload.get("sub")
        if not username:
            return {
                "code": 401,
                "message": "无效的令牌",
                "data": {"valid": False}
            }

        return {
            "code": 200,
            "message": "令牌有效",
            "data": {
                "valid": True,
                "username": username,
                "type": payload.get("type", "access"),
                "exp": payload.get("exp")
            }
        }
    except Exception as e:
        logger.error(f"验证令牌失败: {e}")
        return {
            "code": 500,
            "message": "验证令牌失败",
            "data": {"valid": False}
        }
