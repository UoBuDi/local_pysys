import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import load_config
from database import create_db_connection

def update_menu_titles():
    config = load_config()
    db_config = config['LOCAL_DB']
    
    conn = create_db_connection(db_config)
    if not conn:
        print("数据库连接失败！")
        return
    
    try:
        with conn.cursor() as cursor:
            # 更新数据查询菜单
            cursor.execute("""
                UPDATE menus 
                SET title = 'dataQuery' 
                WHERE name = '数据查询' OR name = 'DataQuery'
            """)
            print(f"更新了 {cursor.rowcount} 条数据查询菜单记录")
            
            # 更新拆分匹配菜单
            cursor.execute("""
                UPDATE menus 
                SET title = 'splitMatch' 
                WHERE name = '拆分匹配' OR name = 'SplitMatch'
            """)
            print(f"更新了 {cursor.rowcount} 条拆分匹配菜单记录")
            
            # 更新详单查询菜单
            cursor.execute("""
                UPDATE menus 
                SET title = 'detailQuery' 
                WHERE name = '详单查询' OR name = 'DetailQuery'
            """)
            print(f"更新了 {cursor.rowcount} 条详单查询菜单记录")
        
        conn.commit()
        print("菜单标题已更新为国际化key！")
    except Exception as e:
        conn.rollback()
        print(f"更新失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_menu_titles()
