"""
角色管理路由
包含角色的增删改查以及菜单和权限获取接口
"""

import logging

import pymysql
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.dependencies import get_db
from core.models import RoleCreateRequest, RoleUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/roles/")
async def get_roles(
    pageIndex: int = 1,
    pageSize: int = 10,
    db=Depends(get_db)
):
    """获取角色列表（支持分页）"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM roles ORDER BY id")
            all_roles = cursor.fetchall()

            for role in all_roles:
                cursor.execute(
                    "SELECT menu_id FROM role_menus WHERE role_id = %s",
                    (role['id'],)
                )
                role_menus = cursor.fetchall()
                role['menus'] = [menu['menu_id'] for menu in role_menus]

                cursor.execute(
                    "SELECT permission_id FROM role_permissions WHERE role_id = %s",
                    (role['id'],)
                )
                role_perms = cursor.fetchall()
                role['permissions'] = [perm['permission_id'] for perm in role_perms]

            total = len(all_roles)
            start = (pageIndex - 1) * pageSize
            end = start + pageSize
            paginated_roles = all_roles[start:end]

            return {
                "code": 200,
                "message": "success",
                "data": {
                    "list": paginated_roles,
                    "total": total,
                    "pageIndex": pageIndex,
                    "pageSize": pageSize
                }
            }
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        return {"code": 500, "message": "获取角色列表失败"}


@router.post("/api/roles/")
async def create_role(role: RoleCreateRequest, db=Depends(get_db)):
    """创建新角色"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM roles WHERE code = %s", (role.code,))
            if cursor.fetchone():
                return {"code": 400, "message": "角色编码已存在"}

            cursor.execute(
                "INSERT INTO roles (name, code, description, status) VALUES (%s, %s, %s, %s)",
                (role.name, role.code, role.description, role.status)
            )
            db.commit()

            return {"code": 200, "message": "角色创建成功"}
    except Exception as e:
        logger.error(f"创建角色失败: {e}")
        return {"code": 500, "message": "创建角色失败"}


@router.put("/api/roles/{role_id}")
async def update_role(role_id: int, role: RoleUpdateRequest, db=Depends(get_db)):
    """更新角色信息"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "角色不存在"}

            cursor.execute("SELECT id FROM roles WHERE code = %s AND id != %s", (role.code, role_id))
            if cursor.fetchone():
                return {"code": 400, "message": "角色编码已存在"}

            cursor.execute(
                "UPDATE roles SET name=%s, code=%s, description=%s, status=%s WHERE id=%s",
                (role.name, role.code, role.description, role.status, role_id)
            )
            db.commit()

            return {"code": 200, "message": "角色更新成功"}
    except Exception as e:
        logger.error(f"更新角色失败: {e}")
        return {"code": 500, "message": "更新角色失败"}


@router.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, db=Depends(get_db)):
    """删除角色（使用事务保护多步操作）"""
    try:
        from database import transaction

        with transaction(db):
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
                if not cursor.fetchone():
                    raise ValueError("ROLE_NOT_FOUND")

                cursor.execute("DELETE FROM role_menus WHERE role_id = %s", (role_id,))
                cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
                cursor.execute("DELETE FROM user_roles WHERE role_id = %s", (role_id,))
                cursor.execute("DELETE FROM roles WHERE id = %s", (role_id,))

            return {"code": 200, "message": "角色删除成功"}

    except ValueError as ve:
        if str(ve) == "ROLE_NOT_FOUND":
            return {"code": 404, "message": "角色不存在"}
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {e}")
        return {"code": 500, "message": "删除角色失败"}


@router.get("/api/roles/{role_id}/menus")
async def get_role_menus(role_id: int, db=Depends(get_db)):
    """获取指定角色的菜单ID列表"""
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT menu_id FROM role_menus WHERE role_id = %s",
                (role_id,)
            )
            menus = cursor.fetchall()

            menu_ids = [menu[0] for menu in menus]

            return {
                "code": 200,
                "message": "success",
                "data": menu_ids
            }
    except Exception as e:
        logger.error(f"获取角色菜单失败: {e}")
        return {"code": 500, "message": "获取角色菜单失败"}


@router.get("/api/roles/{role_id}/permissions")
async def get_role_permissions(role_id: int, db=Depends(get_db)):
    """获取指定角色的权限点ID列表"""
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT permission_id FROM role_permissions WHERE role_id = %s",
                (role_id,)
            )
            permissions = cursor.fetchall()

            permission_ids = [perm[0] for perm in permissions]

            return {
                "code": 200,
                "message": "success",
                "data": permission_ids
            }
    except Exception as e:
        logger.error(f"获取角色权限失败: {e}")
        return {"code": 500, "message": "获取角色权限失败"}
