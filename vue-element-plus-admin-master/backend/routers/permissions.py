"""
权限管理路由
包含权限点的增删改查接口
"""

import logging

import pymysql
from fastapi import APIRouter, Depends

from core.dependencies import get_db
from core.models import PermissionCreateRequest, PermissionUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/permissions/")
async def get_permissions(db=Depends(get_db)):
    """获取所有权限点列表（含所属菜单名称）"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT p.*, m.name AS menu_name
                FROM permissions p
                LEFT JOIN menus m ON p.menu_id = m.id
                ORDER BY p.id
            """)
            permissions = cursor.fetchall()
            
            return {
                "code": 200,
                "message": "success",
                "data": permissions
            }
    except Exception as e:
        logger.error(f"获取权限点列表失败: {e}")
        return {"code": 500, "message": "获取权限点列表失败"}


@router.post("/api/permissions/")
async def create_permission(permission: PermissionCreateRequest, db=Depends(get_db)):
    """创建新权限点"""
    try:
        with db.cursor() as cursor:
            # 检查权限编码是否已存在
            cursor.execute("SELECT id FROM permissions WHERE code = %s", (permission.code,))
            if cursor.fetchone():
                return {"code": 400, "message": "权限编码已存在"}
            
            # 插入新权限点
            cursor.execute(
                """INSERT INTO permissions (code, name, module, resource, operation, description, status, menu_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (permission.code, permission.name, permission.module,
                 permission.resource, permission.operation, 
                 permission.description, permission.status, permission.menu_id)
            )
            db.commit()
            
            return {"code": 200, "message": "权限点创建成功"}
    except Exception as e:
        logger.error(f"创建权限点失败: {e}")
        return {"code": 500, "message": "创建权限点失败"}


@router.put("/api/permissions/{permission_id}")
async def update_permission(permission_id: int, permission: PermissionUpdateRequest, db=Depends(get_db)):
    """更新权限点信息"""
    try:
        with db.cursor() as cursor:
            # 检查权限点是否存在
            cursor.execute("SELECT id FROM permissions WHERE id = %s", (permission_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "权限点不存在"}
            
            # 更新权限点信息
            cursor.execute(
                """UPDATE permissions SET name=%s, module=%s, resource=%s, operation=%s, description=%s, status=%s, menu_id=%s
                   WHERE id=%s""",
                (permission.name, permission.module, permission.resource,
                 permission.operation, permission.description, 
                 permission.status, permission.menu_id, permission_id)
            )
            db.commit()
            
            return {"code": 200, "message": "权限点更新成功"}
    except Exception as e:
        logger.error(f"更新权限点失败: {e}")
        return {"code": 500, "message": "更新权限点失败"}


@router.delete("/api/permissions/{permission_id}")
async def delete_permission(permission_id: int, db=Depends(get_db)):
    """删除权限点"""
    try:
        with db.cursor() as cursor:
            # 检查权限点是否存在
            cursor.execute("SELECT id FROM permissions WHERE id = %s", (permission_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "权限点不存在"}
            
            # 删除角色权限关联
            cursor.execute("DELETE FROM role_permissions WHERE permission_id = %s", (permission_id,))
            
            # 删除权限点
            cursor.execute("DELETE FROM permissions WHERE id = %s", (permission_id,))
            db.commit()
            
            return {"code": 200, "message": "权限点删除成功"}
    except Exception as e:
        logger.error(f"删除权限点失败: {e}")
        return {"code": 500, "message": "删除权限点失败"}
