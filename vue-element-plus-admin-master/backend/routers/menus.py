"""
菜单管理路由
包含菜单的增删改查接口以及数据格式转换辅助函数
"""

import json
import logging

import pymysql
from fastapi import APIRouter, Depends
from typing import Optional, List, Dict, Any

from core.dependencies import get_db
from core.models import MenuCreateRequest, MenuUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_camel(name: str) -> str:
    """将下划线命名转为驼峰命名"""
    parts = name.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def _row_to_frontend(row: dict) -> dict:
    """
    将数据库行转换为前端期望的格式

    转换规则：
    - 所有字段名转为驼峰命名
    - meta_json 展开为 meta 嵌套对象
    - 从 meta 中提取 title 作为顶层字段
    - permission 转换为 permissionList 数组格式
    - 保留 children 占位供前端构建树形
    """
    result = {}
    for key, value in row.items():
        camel_key = _to_camel(key)
        if key == 'meta_json':
            continue
        result[camel_key] = value

    meta_raw = row.get('meta_json')
    meta = {}
    if meta_raw is not None:
        if isinstance(meta_raw, str):
            try:
                meta = json.loads(meta_raw)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        elif isinstance(meta_raw, dict):
            meta = meta_raw

    if not meta.get('title') and result.get('name'):
        meta['title'] = result['name']
    if not meta.get('icon') and row.get('icon'):
        meta['icon'] = row['icon']

    result['meta'] = meta
    result['title'] = meta.get('title', result.get('name', ''))

    permission_str = row.get('permission', '')
    if permission_str:
        result['permissionList'] = [
            {
                'id': 1,
                'value': permission_str,
                'label': permission_str.split(':')[-1] if ':' in permission_str else permission_str
            }
        ]
    else:
        result['permissionList'] = []

    if 'children' not in result:
        result['children'] = []

    return result


def _build_menu_tree(items: list, parent_id: int = 0) -> list:
    """
    将扁平菜单列表构建为树形结构

    Args:
        items: 已转换为前端格式的菜单列表
        parent_id: 父级ID

    Returns:
        树形结构的菜单列表
    """
    tree = []
    for item in items:
        if item.get('parentId') == parent_id:
            node = {**item}
            children = _build_menu_tree(items, item['id'])
            if children:
                node['children'] = children
            else:
                del node['children']
            tree.append(node)
    return tree


@router.get("/api/menus/")
async def get_menus(db=Depends(get_db)):
    """获取所有菜单列表（扁平格式，含 meta 展开和驼峰命名）"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM menus ORDER BY sort_order")
            rows = cursor.fetchall()

            flat_list = [_row_to_frontend(row) for row in rows]
            menu_tree = _build_menu_tree(flat_list)

            return {
                "code": 200,
                "message": "success",
                "data": {
                    "list": flat_list
                }
            }
    except Exception as e:
        logger.error(f"获取菜单列表失败: {e}")
        return {"code": 500, "message": "获取菜单列表失败"}


def _extract_meta_from_form(form_data: dict) -> dict:
    """
    从前端表单数据中提取 meta 对象

    前端表单使用 meta.title, meta.icon 等嵌套路径，
    需要合并 icon 顶层字段和 meta_json 中已有的字段
    """
    meta = {}
    meta_fields = ['title', 'icon', 'activeMenu', 'hidden', 'alwaysShow',
                   'noCache', 'breadcrumb', 'affix', 'noTagsView', 'canTo']

    for field in meta_fields:
        meta_key = f'meta.{field}'
        if meta_key in form_data and form_data[meta_key] is not None:
            meta[field] = form_data[meta_key]

    if not meta.get('title') and form_data.get('name'):
        meta['title'] = form_data['name']
    if not meta.get('icon') and form_data.get('icon'):
        meta['icon'] = form_data['icon']

    return meta


def _extract_permission_from_form(form_data: dict) -> str:
    """
    从前端表单的 permissionList 提取权限字符串

    permissionList 是 [{id, value, label}] 数组，
    数据库存储为逗号分隔的权限字符串
    """
    permission_list = form_data.get('permissionList', [])
    if isinstance(permission_list, list) and permission_list:
        values = []
        for item in permission_list:
            if isinstance(item, dict) and item.get('value'):
                values.append(item['value'])
            elif isinstance(item, str):
                values.append(item)
        return ','.join(values)
    if isinstance(form_data.get('permission'), str):
        return form_data['permission']
    return ''


@router.post("/api/menus/")
async def create_menu(menu: MenuCreateRequest, db=Depends(get_db)):
    """创建新菜单"""
    try:
        form_data = menu.model_dump(exclude_none=True)
        meta = _extract_meta_from_form(form_data)
        permission = _extract_permission_from_form(form_data)

        with db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO menus
                   (name, route_name, i18n_key, icon, path, component, parent_id, type,
                    meta_json, permission, sort_order, status, visible,
                    always_show, no_cache, affix, can_to)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    form_data.get('name', ''),
                    form_data.get('routeName') or form_data.get('name', ''),
                    form_data.get('i18nKey'),
                    form_data.get('icon') or meta.get('icon', ''),
                    form_data.get('path', ''),
                    form_data.get('component'),
                    form_data.get('parentId', 0),
                    form_data.get('type', 1),
                    json.dumps(meta, ensure_ascii=False) if meta else None,
                    permission or None,
                    form_data.get('sortOrder', 0),
                    form_data.get('status', 1),
                    form_data.get('visible', 1),
                    1 if meta.get('alwaysShow') else 0,
                    1 if meta.get('noCache') else 0,
                    1 if meta.get('affix') else 0,
                    1 if meta.get('canTo', True) else 0,
                )
            )
            db.commit()

            return {"code": 200, "message": "菜单创建成功"}
    except Exception as e:
        logger.error(f"创建菜单失败: {e}")
        return {"code": 500, "message": f"菜单创建失败: {str(e)}"}


@router.put("/api/menus/{menu_id}")
async def update_menu(menu_id: int, menu: MenuUpdateRequest, db=Depends(get_db)):
    """更新菜单信息"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM menus WHERE id = %s", (menu_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "菜单不存在"}

            form_data = menu.model_dump(exclude_none=True)
            meta = _extract_meta_from_form(form_data)
            permission = _extract_permission_from_form(form_data)

            cursor.execute(
                """UPDATE menus SET
                   name=%s, route_name=%s, i18n_key=%s, icon=%s, path=%s, component=%s,
                   parent_id=%s, type=%s, meta_json=%s, permission=%s,
                   sort_order=%s, status=%s, visible=%s,
                   always_show=%s, no_cache=%s, affix=%s, can_to=%s
                   WHERE id=%s""",
                (
                    form_data.get('name', ''),
                    form_data.get('routeName') or form_data.get('name', ''),
                    form_data.get('i18nKey'),
                    form_data.get('icon') or meta.get('icon', ''),
                    form_data.get('path', ''),
                    form_data.get('component'),
                    form_data.get('parentId', 0),
                    form_data.get('type', 1),
                    json.dumps(meta, ensure_ascii=False) if meta else None,
                    permission or None,
                    form_data.get('sortOrder', 0),
                    form_data.get('status', 1),
                    form_data.get('visible', 1),
                    1 if meta.get('alwaysShow') else 0,
                    1 if meta.get('noCache') else 0,
                    1 if meta.get('affix') else 0,
                    1 if meta.get('canTo', True) else 0,
                    menu_id,
                )
            )
            db.commit()

            return {"code": 200, "message": "菜单更新成功"}
    except Exception as e:
        logger.error(f"更新菜单失败: {e}")
        return {"code": 500, "message": f"菜单更新失败: {str(e)}"}


@router.delete("/api/menus/{menu_id}")
async def delete_menu(menu_id: int, db=Depends(get_db)):
    """删除菜单（同时删除子菜单）"""
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM menus WHERE id = %s", (menu_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "菜单不存在"}

            cursor.execute("""
                DELETE FROM role_menus WHERE menu_id IN (
                    SELECT id FROM menus WHERE id = %s OR parent_id = %s
                )
            """, (menu_id, menu_id))

            cursor.execute("DELETE FROM menus WHERE parent_id = %s", (menu_id,))
            cursor.execute("DELETE FROM menus WHERE id = %s", (menu_id,))
            db.commit()

            return {"code": 200, "message": "菜单删除成功"}
    except Exception as e:
        logger.error(f"删除菜单失败: {e}")
        return {"code": 500, "message": "菜单删除失败"}
