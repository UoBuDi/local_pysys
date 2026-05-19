#!/usr/bin/env python3
import pymysql
import sys

# 数据库连接配置
db_config = {
    'host': '172.32.48.238',
    'port': 3306,
    'user': 'root',
    'password': '9a1d4e4ae72d2eaa',
    'database': 'branchdb',
    'charset': 'utf8mb4'
}

try:
    # 连接数据库
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 查询表是否存在
    cursor.execute("SHOW TABLES LIKE 'gbupload_etctu_as_2025%'")
    tables = cursor.fetchall()
    
    if not tables:
        print("未找到匹配的表")
        sys.exit(0)
    
    print("找到匹配的表:")
    for table in tables:
        print(f"- {table['Tables_in_branchdb']}")
    
    # 查询指定表结构
    print("\n查询表结构:")
    cursor.execute("DESCRIBE gbupload_etctu_as_20251001")
    columns = cursor.fetchall()
    
    print("\n表结构详情:")
    print(f"{'字段名':<20} {'类型':<20} {'是否为空':<10} {'键':<10} {'默认值':<15} {'额外信息':<15}")
    print("-" * 90)
    for col in columns:
        field = col['Field']
        type_ = col['Type']
        null = col['Null']
        key = col['Key']
        default = col['Default'] if col['Default'] is not None else ''
        extra = col['Extra']
        print(f"{field:<20} {type_:<20} {null:<10} {key:<10} {default:<15} {extra:<15}")
    
    # 查询表索引
    print("\n表索引:")
    cursor.execute("SHOW INDEX FROM gbupload_etctu_as_20251001")
    indexes = cursor.fetchall()
    if indexes:
        for idx in indexes:
            print(f"- 索引名: {idx['Key_name']}, 字段: {idx['Column_name']}, 索引类型: {idx['Index_type']}")
    else:
        print("- 无索引")
    
    # 查询表数据行数
    cursor.execute("SELECT COUNT(*) as count FROM gbupload_etctu_as_20251001")
    row_count = cursor.fetchone()
    print(f"\n表数据行数: {row_count['count']}")
    
    # 查询表的创建语句
    cursor.execute("SHOW CREATE TABLE gbupload_etctu_as_20251001")
    create_table = cursor.fetchone()
    print(f"\n表创建语句:\n{create_table['Create Table']}")
    
except Exception as e:
    print(f"执行失败: {e}")
    sys.exit(1)
finally:
    # 关闭数据库连接
    if conn:
        cursor.close()
        conn.close()
