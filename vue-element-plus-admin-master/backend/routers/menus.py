"""
菜单管理路由
包含菜单的增删改查接口以及构建菜单树辅助函数
"""

import logging

import pymysql
from fastapi import APIRouter, Depends
from typing import Optional

from core.dependencies import get_db
from core.models import MenuCreateRequest, MenuUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def build_menu_tree(menus: list, parent_id: int = 0) -> list:
    """
    构建菜单树结构
    
    Args:
        menus: 菜单列表
        parent_id: 父级ID
    
    Returns:
        树形结构的菜单列表
    """
    tree = []
    
    for menu in menus:
        if menu.get('parent_id') == parent_id:
            node = menu.copy()
            children = build_menu_tree(menus, menu['id'])
            if children:
                node['children'] = children
            tree.append(node)
    
    return tree


@router.get("/api/menus/")
async def get_menus(db=Depends(get_db)):
    """获取所有菜单列表（树形结构）"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM menus ORDER BY sort_order")
            menus = cursor.fetchall()
            
            # 构建菜单树
            menu_tree = build_menu_tree(menus)
            
            return {
                "code": 200,
                "message": "success",
                "data": menu_tree
            }
    except Exception as e:
        logger.error(f"获取菜单列表失败: {e}")
        return {"code": 500, "message": "获取菜单列表失败"}


@router.post("/api/menus/")
async def create_menu(menu: MenuCreateRequest, db=Depends(get_db)):
    """创建新菜单"""
    try:
        with db.cursor() as cursor:
            # 插入新菜单
            cursor.execute(
                """INSERT INTO menus (name, icon, path, component, parent_id, sort_order, status, visible) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (menu.name, menu.icon, menu.path, menu.component, 
                 menu.parent_id, menu.sort_order, menu.status, menu.visible)
            )
            db.commit()
            
            return {"code": 200, "message": "菜单创建成功"}
    except Exception as e:
        logger.error(f"创建菜单失败: {e}")
        return {"code": 500, "message": "创建菜单失败"}


@router.put("/api/menus/{menu_id}")
async def update_menu(menu_id: int, menu: MenuUpdateRequest, db=Depends(get_db)):
    """更新菜单信息"""
    try:
        with db.cursor() as cursor:
            # 检查菜单是否存在
            cursor.execute("SELECT id FROM menus WHERE id = %s", (menu_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "菜单不存在"}
            
            # 更新菜单信息
            cursor.execute(
                """UPDATE menus SET name=%s, icon=%s, path=%s, component=%s, parent_id=%s, sort_order=%s, status=%s, visible=%s 
                   WHERE id=%s""",
                (menu.name, menu.icon, menu.path, menu.component,
                 menu.parent_id, menu.sort_order, menu.status, menu.visible, menu_id)
            )
            db.commit()
            
            return {"code": 200, "message": "菜单更新成功"}
    except Exception as e:
        logger.error(f"更新菜单失败: {e}")
        return {"code": 500, "message": "更新菜单失败"}


@router.delete("/api/menus/{menu_id}")
async def delete_menu(menu_id: int, db=Depends(get_db)):
    """删除菜单（同时删除子菜单）"""
    try:
        with db.cursor() as cursor:
            # 检查菜单是否存在
            cursor.execute("SELECT id FROM menus WHERE id = %s", (menu_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "菜单不存在"}
            
            # 删除角色菜单关联（包含子菜单）
            cursor.execute("""
                DELETE FROM role_menus WHERE menu_id IN (
                    SELECT id FROM menus WHERE id = %s OR parent_id = %s
                )
            """, (menu_id, menu_id))
            
            # 删除子菜单
            cursor.execute("DELETE FROM menus WHERE parent_id = %s", (menu_id,))
            
            # 删除当前菜单
            cursor.execute("DELETE FROM menus WHERE id = %s", (menu_id,))
            db.commit()
            
            return {"code": 200, "message": "菜单删除成功"}
    except Exception as e:
        logger.error(f"删除菜单失败: {e}")
        return {"code": 500, "message": "删除菜单失败"}
