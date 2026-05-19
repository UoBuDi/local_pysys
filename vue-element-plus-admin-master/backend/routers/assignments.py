"""
关联分配路由
包含用户-角色、角色-菜单、角色-权限的关联分配接口（使用事务保护）
"""

import logging

import pymysql
from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_db
from core.models import AssignRoleRequest, AssignMenuRequest, AssignPermissionRequest
from database import transaction

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/user-roles/")
async def assign_user_roles(request: AssignRoleRequest, db=Depends(get_db)):
    """为用户分配角色（批量，使用事务保护）"""
    try:
        with transaction(db):
            with db.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE id = %s", (request.user_id,))
                if not cursor.fetchone():
                    raise ValueError("USER_NOT_FOUND")

                cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (request.user_id,))

                if request.role_ids:
                    values = [(request.user_id, role_id) for role_id in request.role_ids]
                    cursor.executemany(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                        values
                    )

            return {"code": 200, "message": "角色分配成功"}

    except ValueError as ve:
        if str(ve) == "USER_NOT_FOUND":
            return {"code": 404, "message": "用户不存在"}
        raise
    except Exception as e:
        logger.error(f"分配用户角色失败: {e}")
        return {"code": 500, "message": "分配用户角色失败"}


@router.get("/api/users/{user_id}/roles")
async def get_user_roles(user_id: int, db=Depends(get_db)):
    """获取指定用户的角色列表"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "用户不存在"}

            cursor.execute("""
                SELECT r.* 
                FROM roles r 
                JOIN user_roles ur ON r.id = ur.role_id 
                WHERE ur.user_id = %s AND r.status = 1
            """, (user_id,))
            roles = cursor.fetchall()

            return {
                "code": 200,
                "message": "success",
                "data": roles
            }
    except Exception as e:
        logger.error(f"获取用户角色失败: {e}")
        return {"code": 500, "message": "获取用户角色失败"}


@router.post("/api/role-menus/")
async def assign_role_menus(request: AssignMenuRequest, db=Depends(get_db)):
    """为角色分配菜单（批量，使用事务保护）"""
    try:
        with transaction(db):
            with db.cursor() as cursor:
                cursor.execute("SELECT id FROM roles WHERE id = %s", (request.role_id,))
                if not cursor.fetchone():
                    raise ValueError("ROLE_NOT_FOUND")

                cursor.execute("DELETE FROM role_menus WHERE role_id = %s", (request.role_id,))

                if request.menu_ids:
                    values = [(request.role_id, menu_id) for menu_id in request.menu_ids]
                    cursor.executemany(
                        "INSERT INTO role_menus (role_id, menu_id) VALUES (%s, %s)",
                        values
                    )

            return {"code": 200, "message": "菜单分配成功"}

    except ValueError as ve:
        if str(ve) == "ROLE_NOT_FOUND":
            return {"code": 404, "message": "角色不存在"}
        raise
    except Exception as e:
        logger.error(f"分配角色菜单失败: {e}")
        return {"code": 500, "message": "分配角色菜单失败"}


@router.post("/api/role-permissions/")
async def assign_role_permissions(request: AssignPermissionRequest, db=Depends(get_db)):
    """为角色分配权限点（批量，使用事务保护）"""
    try:
        with transaction(db):
            with db.cursor() as cursor:
                cursor.execute("SELECT id FROM roles WHERE id = %s", (request.role_id,))
                if not cursor.fetchone():
                    raise ValueError("ROLE_NOT_FOUND")

                cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (request.role_id,))

                if request.permission_ids:
                    values = [(request.role_id, perm_id) for perm_id in request.permission_ids]
                    cursor.executemany(
                        "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                        values
                    )

            return {"code": 200, "message": "权限分配成功"}

    except ValueError as ve:
        if str(ve) == "ROLE_NOT_FOUND":
            return {"code": 404, "message": "角色不存在"}
        raise
    except Exception as e:
        logger.error(f"分配角色权限失败: {e}")
        return {"code": 500, "message": "分配角色权限失败"}
