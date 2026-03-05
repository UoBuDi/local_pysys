#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新数据库中菜单名称为国际化key
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import load_config
import pymysql


def update_menu_names():
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
            # 先查看当前菜单数据
            cursor.execute("SELECT id, name, path FROM menus ORDER BY sort_order")
            print("当前菜单数据：")
            for row in cursor.fetchall():
                print(row)
            
            print("\n开始更新...")
            
            # 更新数据查询菜单
            cursor.execute("""
                UPDATE menus 
                SET name = 'dataQuery' 
                WHERE (name = '数据查询' OR name = 'DataQuery') AND path = '/data-query'
            """)
            print(f"更新了 {cursor.rowcount} 条数据查询菜单记录")
            
            # 更新拆分匹配菜单
            cursor.execute("""
                UPDATE menus 
                SET name = 'splitMatch' 
                WHERE (name = '拆分匹配' OR name = 'SplitMatch') AND path = 'split-match'
            """)
            print(f"更新了 {cursor.rowcount} 条拆分匹配菜单记录")
            
            # 更新详单查询菜单
            cursor.execute("""
                UPDATE menus 
                SET name = 'detailQuery' 
                WHERE (name = '详单查询' OR name = 'DetailQuery') AND path = 'detail-query'
            """)
            print(f"更新了 {cursor.rowcount} 条详单查询菜单记录")
            
            # 查看更新结果
            cursor.execute("SELECT id, name, path FROM menus ORDER BY sort_order")
            print("\n更新后的菜单数据：")
            for row in cursor.fetchall():
                print(row)
        
        conn.commit()
        print("\n菜单名称已更新为国际化key！")
        conn.close()
    except Exception as e:
        print(f"更新失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_menu_names()
