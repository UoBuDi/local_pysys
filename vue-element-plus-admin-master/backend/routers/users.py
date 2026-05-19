"""
用户管理路由
包含用户的增删改查以及菜单和权限获取接口
"""

import logging

import pymysql
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.dependencies import get_db, get_current_user
from core.models import UserCreateRequest, UserUpdateRequest
from core.security import hash_password
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/users/")
async def get_users(
    department_id: Optional[str] = None,
    pageIndex: int = 1,
    pageSize: int = 10,
    db=Depends(get_db)
):
    """获取用户列表（数据库层面分页，使用 LIMIT/OFFSET）"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            dept_id = int(department_id) if department_id and department_id.isdigit() else None

            where_clause = ""
            params = []
            if dept_id:
                where_clause = "WHERE u.department_id = %s"
                params.append(dept_id)

            count_sql = f"SELECT COUNT(*) FROM users u {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]

            offset = (pageIndex - 1) * pageSize
            data_sql = f"""
                SELECT u.*, d.name as department_name 
                FROM users u 
                LEFT JOIN departments d ON u.department_id = d.id 
                {where_clause}
                ORDER BY u.id
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, params + [pageSize, offset])
            paginated_users = cursor.fetchall()

            for user in paginated_users:
                cursor.execute(
                    "SELECT role_id FROM user_roles WHERE user_id = %s",
                    (user['id'],)
                )
                user_roles = cursor.fetchall()
                user['roles'] = [role['role_id'] for role in user_roles]

            return {
                "code": 200,
                "message": "success",
                "data": {
                    "list": paginated_users,
                    "total": total,
                    "pageIndex": pageIndex,
                    "pageSize": pageSize
                }
            }
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return {"code": 500, "message": "获取用户列表失败"}


@router.post("/api/users/")
async def create_user(user: UserCreateRequest, db=Depends(get_db)):
    """创建新用户"""
    try:
        logger.info(f"开始创建用户，接收数据: {user.model_dump()}")

        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
            if cursor.fetchone():
                logger.warning(f"用户名已存在: {user.username}")
                return {"code": 400, "message": "用户名已存在"}

            hashed_password = hash_password(user.password)

            cursor.execute(
                "INSERT INTO users (username, password, nickname, email, department_id, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (user.username, hashed_password, user.nickname, user.email, user.department_id, user.status)
            )
            db.commit()

            logger.info(f"用户创建成功，生成ID: {cursor.lastrowid}")
            return {"code": 200, "message": "用户创建成功"}
    except Exception as e:
        logger.error(f"创建用户失败: {e}", exc_info=True)
        return {"code": 500, "message": "创建用户失败"}


@router.put("/api/users/{user_id}")
async def update_user(user_id: int, user: UserUpdateRequest, db=Depends(get_db)):
    """更新用户信息"""
    try:
        logger.info(f"开始更新用户，用户ID: {user_id}, 接收数据: {user.model_dump()}")

        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                logger.warning(f"用户不存在: {user_id}")
                return {"code": 404, "message": "用户不存在"}

            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (user.username, user_id))
            if cursor.fetchone():
                logger.warning(f"用户名已存在: {user.username}")
                return {"code": 400, "message": "用户名已存在"}

            if user.password:
                hashed_password = hash_password(user.password)

                cursor.execute(
                    "UPDATE users SET username=%s, password=%s, nickname=%s, email=%s, department_id=%s, status=%s WHERE id=%s",
                    (user.username, hashed_password, user.nickname, user.email, user.department_id, user.status, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET username=%s, nickname=%s, email=%s, department_id=%s, status=%s WHERE id=%s",
                    (user.username, user.nickname, user.email, user.department_id, user.status, user_id)
                )

            db.commit()
            logger.info(f"用户更新成功，用户ID: {user_id}, 影响行数: {cursor.rowcount}")
            return {"code": 200, "message": "用户更新成功"}
    except Exception as e:
        logger.error(f"更新用户失败: {e}", exc_info=True)
        return {"code": 500, "message": "更新用户失败"}


@router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db=Depends(get_db)):
    """删除用户"""
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return {"code": 404, "message": "用户不存在"}

            cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            db.commit()

            return {"code": 200, "message": "用户删除成功"}
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        return {"code": 500, "message": "删除用户失败"}


@router.get("/api/user/menus")
async def get_user_menus(credentials=Depends(get_current_user)):
    """获取当前用户的菜单列表（优化为单次 JOIN 查询）"""
    config = get_app_config()

    try:
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                username = credentials["username"]

                cursor.execute("""
                    SELECT DISTINCT m.* 
                    FROM menus m 
                    JOIN role_menus rm ON m.id = rm.menu_id 
                    JOIN user_roles ur ON rm.role_id = ur.role_id 
                    JOIN users u ON ur.user_id = u.id 
                    WHERE u.username = %s AND m.status = 1 AND m.visible = 1 
                    ORDER BY m.sort_order
                """, (username,))
                menus = cursor.fetchall()

                if not menus:
                    return {"code": 200, "message": "success", "data": []}

                converted_menus = []
                menu_map = {menu['id']: menu for menu in menus}
                logger.info(f"菜单查询结果: {len(menus)} 条, IDs: {[m['id'] for m in menus]}")

                title_map = {
                    '数据查询': 'router.dataQuery',
                    '拆分匹配': 'router.splitMatch',
                    '详单查询': 'router.detailQuery',
                    '路径匹配': 'router.pathMatch',
                    '系统管理': 'router.authorization',
                    '用户管理': 'router.user',
                    '角色管理': 'router.role',
                    '菜单管理': 'router.menuManagement',
                    '部门管理': 'router.department',
                    '首页': 'router.dashboard',
                    '工作台': 'router.workplace',
                    '分析页': 'router.analysis',
                    '同步管理': 'router.syncManage',
                    '同步配置': 'router.syncConfig',
                    '同步控制': 'router.syncControl',
                    '系统工具': 'router.systemTools',
                    '定时任务': 'router.scheduledTasks',
                    '数据记录': 'router.dataRecords',
                    '监控中心': 'router.monitorCenter',
                    '特情记录': 'router.specialRecords',
                    '事件记录': 'router.eventRecords',
                    '排班功能': 'router.scheduling',
                    '排班管理': 'router.scheduling',
                    '排班日历': 'router.schedulingCalendar',
                    '班组管理': 'router.schedulingGroups',
                    '人员管理': 'router.schedulingStaff',
                    '班次管理': 'router.schedulingShifts',
                    '管理中心': 'router.manageCenter'
                }

                for menu in menus:
                    if not menu.get('path'):
                        continue

                    converted_menu = menu.copy()

                    if 'sort_order' in converted_menu:
                        converted_menu['sortOrder'] = converted_menu['sort_order']
                    if 'parent_id' in converted_menu:
                        converted_menu['parentId'] = converted_menu['parent_id']

                    if converted_menu.get('parent_id') == 0:
                        converted_menu['component'] = '#'
                    elif converted_menu.get('parent_id') != 0:
                        path_key = converted_menu.get('path', '').lstrip('/')
                        component_mapping = {
                            'analysis': 'Dashboard/Analysis',
                            'workplace': 'Dashboard/Workplace',
                            'split-match': 'SystemTools/SplitMatch',
                            'detail-query': 'SystemTools/DetailQuery',
                            'path-match': 'SystemTools/PathMatch',
                            'config': 'SystemTools/SyncConfig',
                            'sync-config': 'SystemTools/SyncConfig',
                            'control': 'SystemTools/SyncControl',
                            'sync-control': 'SystemTools/SyncControl',
                            'params-config': 'SystemTools/ParamsConfig',
                            'department': 'Authorization/Department/Department',
                            'user': 'Authorization/User/User',
                            'menu': 'Authorization/Menu/Menu',
                            'role': 'Authorization/Role/Role',
                            'scheduled-tasks': 'SystemTools/ScheduledTasks/ScheduledTasks',
                            'monitor-center': 'ParentLayout',
                            'special-records': 'DataRecords/SpecialRecords',
                            'event-records': 'DataRecords/EventRecords',
                            'scheduling': 'ParentLayout',
                            'calendar': 'DataRecords/Scheduling/Calendar',
                            'groups': 'DataRecords/Scheduling/Groups',
                            'staff': 'DataRecords/Scheduling/Staff',
                            'shifts': 'DataRecords/Scheduling/Shifts',
                            'manage-center': 'DataRecords/ManageCenter',
                            'sync-management': 'ParentLayout'
                        }

                        converted_menu['component'] = component_mapping.get(path_key, path_key)
                        converted_menu['path'] = path_key

                    original_name = converted_menu.get('name', '')
                    route_name = converted_menu.get('route_name') or original_name
                    converted_menu['name'] = route_name
                    converted_menu['meta'] = {
                        'title': title_map.get(original_name, original_name),
                        'icon': converted_menu.get('icon', ''),
                        'hidden': not converted_menu.get('visible', 1),
                        'alwaysShow': bool(converted_menu.get('always_show', 0)),
                        'noCache': bool(converted_menu.get('no_cache', 0)),
                        'breadcrumb': True,
                        'affix': bool(converted_menu.get('affix', 0)),
                        'noTagsView': False,
                        'canTo': bool(converted_menu.get('can_to', 1)),
                        'activeMenu': ''
                    }

                    converted_menus.append(converted_menu)

                logger.info(f"转换后菜单: {len(converted_menus)} 条, IDs: {[m['id'] for m in converted_menus]}")
                converted_map = {m['id']: m for m in converted_menus}
                tree_menus = []
                orphan_count = 0
                for m in converted_menus:
                    pid = m.get('parent_id', 0)
                    if pid == 0:
                        m.setdefault('children', [])
                        tree_menus.append(m)
                    else:
                        parent = converted_map.get(pid)
                        if parent:
                            parent.setdefault('children', []).append(m)
                        else:
                            orphan_count += 1
                            logger.warning(f"孤儿菜单: id={m['id']} name={m.get('name','')} parent_id={pid}")

                logger.info(f"树形构建: 顶级={len(tree_menus)}, 孤儿={orphan_count}")
                for tm in tree_menus:
                    child_ids = [c['id'] for c in tm.get('children', [])]
                    logger.info(f"  顶级菜单: id={tm['id']} name={tm.get('name','')} children_ids={child_ids}")

                FIELDS_TO_REMOVE = [
                    'parent_id', 'parentId', 'sort_order', 'sortOrder', 'route_name',
                    'always_show', 'no_cache', 'affix', 'can_to', 'visible', 'icon',
                    'i18n_key', 'meta_json', 'permission', 'status', 'created_at',
                    'updated_at', 'operations', 'type', 'id'
                ]

                def clean_menu_fields(menus):
                    for m in menus:
                        for field in FIELDS_TO_REMOVE:
                            m.pop(field, None)
                        if m.get('children'):
                            clean_menu_fields(m['children'])

                clean_menu_fields(tree_menus)

                def add_redirect_and_always_show(menus, parent_path=''):
                    for m in menus:
                        current_path = m.get('path', '')
                        children = m.get('children', [])
                        if children:
                            first_child_path = children[0].get('path', '')
                            if current_path.startswith('/'):
                                m['redirect'] = f"{current_path}/{first_child_path}"
                            else:
                                if parent_path:
                                    m['redirect'] = f"{parent_path}/{current_path}/{first_child_path}"
                                else:
                                    m['redirect'] = f"/{current_path}/{first_child_path}"
                            if len(children) > 1 or m.get('meta', {}).get('alwaysShow'):
                                m['meta']['alwaysShow'] = True
                            add_redirect_and_always_show(children, current_path if current_path.startswith('/') else (f"{parent_path}/{current_path}" if parent_path else current_path))

                add_redirect_and_always_show(tree_menus)

                return {"code": 200, "message": "success", "data": tree_menus}

    except Exception as e:
        logger.error(f"获取用户菜单失败: {e}")
        return {"code": 500, "message": "获取用户菜单失败"}


@router.get("/api/user/permissions")
async def get_user_permissions(credentials=Depends(get_current_user)):
    """获取当前用户的权限点列表（使用连接池上下文管理器）"""
    config = get_app_config()

    try:
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                username = credentials["username"]

                cursor.execute("""
                    SELECT r.id 
                    FROM users u 
                    JOIN user_roles ur ON u.id = ur.user_id 
                    JOIN roles r ON ur.role_id = r.id 
                    WHERE u.username = %s AND r.status = 1
                """, (username,))
                roles = cursor.fetchall()

                if not roles:
                    return {"code": 200, "message": "success", "data": []}

                role_ids = [role['id'] for role in roles]

                placeholders = ','.join(['%s'] * len(role_ids))
                cursor.execute(f"""
                    SELECT DISTINCT p.code 
                    FROM permissions p 
                    JOIN role_permissions rp ON p.id = rp.permission_id 
                    WHERE rp.role_id IN ({placeholders}) AND p.status = 1
                """, role_ids)
                permissions = [row['code'] for row in cursor.fetchall()]

                return {"code": 200, "message": "success", "data": permissions}

    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        return {"code": 500, "message": "获取用户权限失败"}
