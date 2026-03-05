#!/usr/bin/env python3
import pymysql
import sys

# 数据库连接配置
db_config = {
    'host': '172.32.48.238',
    'port': 3306,
    'user': 'root',
    'password': '9a1d4e4ae72d2eaa',
    'database': 'system_db',
    'charset': 'utf8mb4'
}

# 读取SQL脚本
with open('add_roles.sql', 'r', encoding='utf8') as f:
    sql_script = f.read()

try:
    # 连接数据库
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 执行SQL脚本
    for sql in sql_script.split(';'):
        sql = sql.strip()
        if sql:
            cursor.execute(sql)
    
    # 提交事务
    conn.commit()
    print("SQL脚本执行成功")
    
    # 查询角色表，确认添加成功
    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()
    print("角色列表：")
    for role in roles:
        print(f"ID: {role['id']}, 名称: {role['name']}, 编码: {role['code']}, 状态: {role['status']}")
    
    # 查询admin用户的角色
    cursor.execute("SELECT u.username, r.name FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE u.username = 'admin'")
    user_roles = cursor.fetchall()
    print("\nadmin用户的角色：")
    for user_role in user_roles:
        print(f"用户名: {user_role['username']}, 角色: {user_role['name']}")
    
except Exception as e:
    print(f"SQL脚本执行失败: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    # 关闭数据库连接
    if conn:
        cursor.close()
        conn.close()
