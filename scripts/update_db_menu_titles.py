#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新数据库中菜单标题为国际化key
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import load_config
import pymysql


def update_menu_titles():
    config = load_config()
    db_config = config['LOCAL_DB']
    
    try:
        conn = pymysql.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset=db_config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        
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
            
            # 查看更新结果
            cursor.execute("SELECT id, name, title, path FROM menus WHERE title IN ('dataQuery', 'splitMatch', 'detailQuery')")
            print("\n更新后的菜单数据：")
            for row in cursor.fetchall():
                print(row)
        
        conn.commit()
        print("\n菜单标题已更新为国际化key！")
        conn.close()
    except Exception as e:
        print(f"更新失败: {e}")


if __name__ == "__main__":
    update_menu_titles()
