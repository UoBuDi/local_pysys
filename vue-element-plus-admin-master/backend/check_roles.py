import pymysql
from dotenv import load_dotenv
import os

load_dotenv()
conn = pymysql.connect(
    host=os.getenv('LOCAL_DB_HOST', '127.0.0.1'),
    port=int(os.getenv('LOCAL_DB_PORT', 3306)),
    user=os.getenv('LOCAL_DB_USER', 'root'),
    password=os.getenv('LOCAL_DB_PASSWORD', '123456'),
    database=os.getenv('LOCAL_DB_NAME', 'local_pysys_db'),
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cursor:
        print('=== 所有角色 ===')
        cursor.execute('SELECT * FROM roles')
        roles = cursor.fetchall()
        for role in roles:
            print(f'角色ID: {role["id"]}, 角色名: {role["name"]}')
        
        print('\n=== 角色-菜单关联 ===')
        cursor.execute('SELECT * FROM role_menus')
        role_menus = cursor.fetchall()
        for rm in role_menus:
            print(f'角色ID: {rm["role_id"]}, 菜单ID: {rm["menu_id"]}')
        
        print('\n=== 用户 admin 的角色 ===')
        cursor.execute('SELECT * FROM users WHERE username = %s', ('admin',))
        user = cursor.fetchone()
        if user:
            cursor.execute('SELECT r.* FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = %s', (user['id'],))
            user_roles = cursor.fetchall()
            for ur in user_roles:
                print(f'角色ID: {ur["id"]}, 角色名: {ur["name"]}')
finally:
    conn.close()
