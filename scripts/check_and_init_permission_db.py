#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并初始化权限管理相关数据库表和数据
"""

import sys
import os
import hashlib

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import load_config
from database import create_db_connection


def check_table_exists(conn, table_name):
    """检查表是否存在"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"检查 {table_name} 表失败: {e}")
        return False


def check_table_structure(conn, table_name, expected_columns):
    """检查表结构"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            existing_columns = [col['Field'] for col in columns]
            
            missing_columns = [col for col in expected_columns if col not in existing_columns]
            extra_columns = [col for col in existing_columns if col not in expected_columns]
            
            return missing_columns, extra_columns
    except Exception as e:
        print(f"检查 {table_name} 表结构失败: {e}")
        return [], []


def create_tables(conn):
    """创建权限管理相关表"""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"Schema文件不存在: {schema_path}")
        return False
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_text = f.read()
        
        statements = [s.strip() for s in sql_text.split(';') if s.strip()]
        
        with conn.cursor() as cursor:
            for stmt in statements:
                if not stmt.startswith('--'):
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        print(f"执行SQL失败: {e}")
                        print(f"SQL: {stmt}")
        
        conn.commit()
        print("表创建成功")
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        conn.rollback()
        return False


def init_default_data(conn):
    """初始化默认数据"""
    try:
        with conn.cursor() as cursor:
            # 1. 检查并创建默认部门
            cursor.execute("SELECT id FROM departments WHERE name = '技术部'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO departments (name, parent_id, sort_order, status) 
                    VALUES ('技术部', 0, 1, 1)
                """)
                print("创建默认部门: 技术部")
            
            # 2. 检查并创建默认角色
            # 超级管理员
            cursor.execute("SELECT id FROM roles WHERE code = 'super_admin'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO roles (name, code, description, status) 
                    VALUES ('超级管理员', 'super_admin', '拥有所有权限', 1)
                """)
                print("创建角色: 超级管理员")
            
            # 管理员
            cursor.execute("SELECT id FROM roles WHERE code = 'admin'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO roles (name, code, description, status) 
                    VALUES ('管理员', 'admin', '管理员权限', 1)
                """)
                print("创建角色: 管理员")
            
            # 普通用户
            cursor.execute("SELECT id FROM roles WHERE code = 'user'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO roles (name, code, description, status) 
                    VALUES ('普通用户', 'user', '普通用户权限', 1)
                """)
                print("创建角色: 普通用户")
            
            # 3. 检查并创建默认菜单
            # 首页 (Dashboard) - 排序设置为0，确保显示在最前面
            cursor.execute("SELECT id FROM menus WHERE name = '首页' AND parent_id = 0")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                    VALUES (0, '首页', 'Dashboard', '/dashboard', NULL, NULL, 0, 1, 1)
                """)
                print("创建菜单: 首页")
            
            # 获取首页菜单ID
            cursor.execute("SELECT id FROM menus WHERE name = '首页' AND parent_id = 0")
            dashboard_menu = cursor.fetchone()
            if dashboard_menu:
                dashboard_menu_id = dashboard_menu['id']
                
                # 分析页面
                cursor.execute("SELECT id FROM menus WHERE name = '分析页' AND parent_id = %s", (dashboard_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '分析页', NULL, 'analysis', 'dashboard/Analysis', NULL, 1, 1, 1)
                    """, (dashboard_menu_id,))
                    print("创建菜单: 分析页")
                
                # 工作台
                cursor.execute("SELECT id FROM menus WHERE name = '工作台' AND parent_id = %s", (dashboard_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '工作台', NULL, 'workplace', 'dashboard/Workplace', NULL, 2, 1, 1)
                    """, (dashboard_menu_id,))
                    print("创建菜单: 工作台")
            
            # 系统管理
            cursor.execute("SELECT id FROM menus WHERE name = '系统管理' AND parent_id = 0")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                    VALUES (0, '系统管理', 'Setting', '/system', NULL, NULL, 1, 1, 1)
                """)
                print("创建菜单: 系统管理")
            
            # 获取系统管理菜单ID
            cursor.execute("SELECT id FROM menus WHERE name = '系统管理' AND parent_id = 0")
            system_menu = cursor.fetchone()
            if system_menu:
                system_menu_id = system_menu['id']
                
                # 用户管理
                cursor.execute("SELECT id FROM menus WHERE name = '用户管理' AND parent_id = %s", (system_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '用户管理', 'User', 'user', 'system/user/index', 'system:user:list', 1, 1, 1)
                    """, (system_menu_id,))
                    print("创建菜单: 用户管理")
                
                # 角色管理
                cursor.execute("SELECT id FROM menus WHERE name = '角色管理' AND parent_id = %s", (system_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '角色管理', 'UserFilled', 'role', 'system/role/index', 'system:role:list', 2, 1, 1)
                    """, (system_menu_id,))
                    print("创建菜单: 角色管理")
                
                # 菜单管理
                cursor.execute("SELECT id FROM menus WHERE name = '菜单管理' AND parent_id = %s", (system_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '菜单管理', 'Menu', 'menu', 'system/menu/index', 'system:menu:list', 3, 1, 1)
                    """, (system_menu_id,))
                    print("创建菜单: 菜单管理")
                
                # 部门管理
                cursor.execute("SELECT id FROM menus WHERE name = '部门管理' AND parent_id = %s", (system_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '部门管理', 'OfficeBuilding', 'department', 'system/department/index', 'system:department:list', 4, 1, 1)
                    """, (system_menu_id,))
                    print("创建菜单: 部门管理")
            
            # 系统工具
            cursor.execute("SELECT id FROM menus WHERE name = '系统工具' AND parent_id = 0")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                    VALUES (0, '系统工具', 'Tools', '/tools', NULL, NULL, 2, 1, 1)
                """)
                print("创建菜单: 系统工具")
            
            # 获取系统工具菜单ID
            cursor.execute("SELECT id FROM menus WHERE name = '系统工具' AND parent_id = 0")
            tools_menu = cursor.fetchone()
            if tools_menu:
                tools_menu_id = tools_menu['id']
                
                # 详单查询
                cursor.execute("SELECT id FROM menus WHERE name = '详单查询' AND parent_id = %s", (tools_menu_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                        VALUES (%s, '详单查询', 'Document', 'detail-query', 'SystemTools/DetailQuery', NULL, 1, 1, 1)
                    """, (tools_menu_id,))
                    print("创建菜单: 详单查询")
                
                # 为详单查询添加按钮权限
                cursor.execute("SELECT id FROM menus WHERE name = '详单查询' AND parent_id = %s", (tools_menu_id,))
                detail_query_menu = cursor.fetchone()
                if detail_query_menu:
                    detail_query_id = detail_query_menu['id']
                    
                    # 调试信息按钮权限
                    cursor.execute("SELECT id FROM menus WHERE name = '调试信息' AND parent_id = %s", (detail_query_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                            VALUES (%s, '调试信息', NULL, NULL, NULL, 'detailQuery:debug', 1, 1, 0)
                        """, (detail_query_id,))
                        print("创建菜单按钮权限: 调试信息")
                    
                    # 导出数据按钮权限
                    cursor.execute("SELECT id FROM menus WHERE name = '导出数据' AND parent_id = %s", (detail_query_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
                            VALUES (%s, '导出数据', NULL, NULL, NULL, 'detailQuery:export', 2, 1, 0)
                        """, (detail_query_id,))
                        print("创建菜单按钮权限: 导出数据")
            
            # 4. 检查并创建默认用户
            # admin用户
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            admin_user = cursor.fetchone()
            if not admin_user:
                # 密码: admin123
                hashed_password = hashlib.md5(b'admin123').hexdigest()
                cursor.execute("""
                    INSERT INTO users (username, password, nickname, email, status) 
                    VALUES ('admin', %s, '超级管理员', 'admin@example.com', 1)
                """, (hashed_password,))
                admin_id = cursor.lastrowid
                print("创建用户: admin")
            else:
                admin_id = admin_user['id']
            
            # test用户
            cursor.execute("SELECT id FROM users WHERE username = 'test'")
            test_user = cursor.fetchone()
            if not test_user:
                # 密码: test123
                hashed_password = hashlib.md5(b'test123').hexdigest()
                cursor.execute("""
                    INSERT INTO users (username, password, nickname, email, status) 
                    VALUES ('test', %s, '测试用户', 'test@example.com', 1)
                """, (hashed_password,))
                test_id = cursor.lastrowid
                print("创建用户: test")
            else:
                test_id = test_user['id']
            
            # 5. 为用户分配角色
            # 获取超级管理员角色ID
            cursor.execute("SELECT id FROM roles WHERE code = 'super_admin'")
            super_admin_role = cursor.fetchone()
            if super_admin_role:
                super_admin_role_id = super_admin_role['id']
                
                # 为admin分配超级管理员角色
                cursor.execute("SELECT id FROM user_roles WHERE user_id = %s AND role_id = %s", (admin_id, super_admin_role_id))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO user_roles (user_id, role_id) 
                        VALUES (%s, %s)
                    """, (admin_id, super_admin_role_id))
                    print("为admin用户分配超级管理员角色")
                
                # 为test分配超级管理员角色
                cursor.execute("SELECT id FROM user_roles WHERE user_id = %s AND role_id = %s", (test_id, super_admin_role_id))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO user_roles (user_id, role_id) 
                        VALUES (%s, %s)
                    """, (test_id, super_admin_role_id))
                    print("为test用户分配超级管理员角色")
            
            # 6. 为角色分配菜单权限
            # 获取所有菜单ID
            cursor.execute("SELECT id FROM menus")
            all_menus = cursor.fetchall()
            menu_ids = [menu['id'] for menu in all_menus]
            
            if super_admin_role and menu_ids:
                # 删除现有权限
                cursor.execute("DELETE FROM role_menus WHERE role_id = %s", (super_admin_role_id,))
                
                # 为超级管理员分配所有菜单权限
                for menu_id in menu_ids:
                    cursor.execute("""
                        INSERT INTO role_menus (role_id, menu_id) 
                        VALUES (%s, %s)
                    """, (super_admin_role_id, menu_id))
                print("为超级管理员角色分配所有菜单权限")
        
        conn.commit()
        print("默认数据初始化完成")
        return True
    except Exception as e:
        print(f"初始化默认数据失败: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("权限管理数据库检查和初始化工具")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 创建数据库连接
    conn = create_db_connection("USER_DB", config) or create_db_connection("LOCAL_DB", config)
    
    if not conn:
        print("无法连接到数据库")
        return 1
    
    try:
        # 检查表是否存在
        tables = [
            'departments', 'users', 'roles', 'menus',
            'user_roles', 'role_menus'
        ]
        
        print("\n[1] 检查表是否存在...")
        missing_tables = []
        for table in tables:
            exists = check_table_exists(conn, table)
            status = "✓" if exists else "✗"
            print(f"  {status} {table}")
            if not exists:
                missing_tables.append(table)
        
        # 如果有缺失的表，创建表
        if missing_tables:
            print(f"\n[2] 发现缺失表: {missing_tables}")
            print("[2] 开始创建表...")
            if not create_tables(conn):
                print("[2] 创建表失败")
                return 1
        else:
            print("\n[2] 所有表都已存在")
        
        # 检查并初始化默认数据
        print("\n[3] 检查并初始化默认数据...")
        if not init_default_data(conn):
            print("[3] 初始化默认数据失败")
            return 1
        
        print("\n" + "=" * 60)
        print("权限管理数据库检查和初始化完成！")
        print("=" * 60)
        print("\n默认账号:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  角色: 超级管理员")
        print("\n  用户名: test")
        print("  密码: test123")
        print("  角色: 超级管理员")
        
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
