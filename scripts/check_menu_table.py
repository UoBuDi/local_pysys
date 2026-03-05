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
            cursor.execute('DESCRIBE menus')
            columns = cursor.fetchall()
            
            print('menus表的结构:')
            for col in columns:
                print(f'{col["Field"]} - {col["Type"]} - {col["Null"]} - {col["Key"]} - {col["Default"]} - {col["Extra"]}')
            
            print('\n数据记录:')
            cursor.execute('SELECT * FROM menus ORDER BY id')
            menus = cursor.fetchall()
            for menu in menus:
                print(menu)
                
    except Exception as e:
        print(f'错误: {e}')
    finally:
        conn.close()
