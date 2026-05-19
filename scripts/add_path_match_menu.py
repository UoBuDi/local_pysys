import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import load_config
from database import create_db_connection

config = load_config()
conn = create_db_connection('USER_DB', config) or create_db_connection('LOCAL_DB', config)

if conn:
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, name, path, parent_id, sort_order FROM menus ORDER BY id')
            menus = cursor.fetchall()
            
            print('数据库中的菜单记录:')
            for menu in menus:
                print(f'ID: {menu["id"]}, 名称: {menu["name"]}, 路径: {menu["path"]}, 父级ID: {menu["parent_id"]}, 排序: {menu["sort_order"]}')
            
            data_query_id = None
            for menu in menus:
                if menu['path'] == '/data-query':
                    data_query_id = menu['id']
                    break
            
            if data_query_id:
                print(f'\n找到数据查询菜单，ID: {data_query_id}')
                
                cursor.execute('SELECT id FROM menus WHERE path = %s AND parent_id = %s', 
                             ('path-match', data_query_id))
                existing = cursor.fetchone()
                
                if existing:
                    print(f'路径匹配菜单已存在，ID: {existing["id"]}')
                else:
                    cursor.execute('SELECT MAX(sort_order) as max_sort FROM menus WHERE parent_id = %s', (data_query_id,))
                    result = cursor.fetchone()
                    next_sort = (result['max_sort'] + 1) if result['max_sort'] is not None else 1
                    
                    cursor.execute('''
                        INSERT INTO menus (name, path, component, parent_id, sort_order, icon, permission, status, visible, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ''', ('路径匹配', 'path-match', 'SystemTools/PathMatch', data_query_id, next_sort, None, None, 1, 1))
                    
                    conn.commit()
                    print(f'路径匹配菜单已成功添加，排序: {next_sort}')
            else:
                print('未找到数据查询菜单')
                
    except Exception as e:
        print(f'错误: {e}')
        conn.rollback()
    finally:
        conn.close()
