#!/usr/bin/env python3
"""
数据库表信息查询脚本
用于查找和验证数据表状态
"""

import pymysql
import sys

def get_db_connection():
    """获取数据库连接"""
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        section = 'LOCAL_DB'
        conn = pymysql.connect(
            host=config.get(section, 'host'),
            port=config.getint(section, 'port'),
            user=config.get(section, 'user'),
            password=config.get(section, 'password'),
            database=config.get(section, 'database'),
            charset=config.get(section, 'charset', fallback='utf8mb4'),
            connect_timeout=5,
            read_timeout=30,
            write_timeout=30
        )
        return conn, config
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None, None

def list_all_tables(conn):
    """列出所有表及其空间使用情况"""
    try:
        cursor = conn.cursor()
        
        sql = """
        SELECT 
            table_name,
            engine,
            ROUND(data_length/1024/1024, 2) AS data_mb,
            ROUND(index_length/1024/1024, 2) AS index_mb,
            ROUND((data_length+index_length)/1024/1024, 2) AS total_mb,
            ROUND(data_free/1024/1024, 2) AS free_mb,
            table_rows,
            create_time,
            update_time
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
        ORDER BY (data_length+index_length) DESC
        """
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        print("\n" + "="*100)
        print("📊 数据库中所有表的详细信息")
        print("="*100)
        print(f"{'表名':<35} {'引擎':<8} {'数据(MB)':<10} {'索引(MB)':<10} {'总计(MB)':<10} {'剩余空间(MB)':<12} {'行数':<12}")
        print("-"*100)
        
        for row in results:
            table_name = row[0][:33] + '..' if len(row[0]) > 35 else row[0]
            print(f"{table_name:<35} {row[1]:<8} {row[2]:<10.2f} {row[3]:<10.2f} {row[4]:<10.2f} {row[5]:<12.2f} {row[6]:<12,}")
            
        print(f"\n共找到 {len(results)} 个表")
        return [row[0] for row in results]
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()

def search_table_by_pattern(conn, pattern):
    """根据模式搜索表名"""
    try:
        cursor = conn.cursor()
        
        # 使用LIKE搜索包含特定关键词的表
        sql = f"""
        SELECT 
            table_name,
            ROUND((data_length+index_length)/1024/1024, 2) AS total_mb,
            ROUND(data_free/1024/1024, 2) AS free_mb,
            table_rows
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() AND table_name LIKE %s
        ORDER BY table_name
        """
        
        cursor.execute(sql, (f'%{pattern}%',))
        results = cursor.fetchall()
        
        if results:
            print(f"\n🔍 找到包含 '{pattern}' 的表:")
            print("-"*80)
            for row in results:
                print(f"  - {row[0]} (大小: {row[1]} MB, 剩余: {row[2]} MB, 行数: {row[3]:,})")
            return True
        else:
            print(f"\n⚠️  未找到包含 '{pattern}' 的表")
            return False
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🔍 数据库表信息查询工具")
    print("="*80)
    
    # 获取数据库连接
    conn, config = get_db_connection()
    if not conn:
        return
    
    print("✅ 数据库连接成功")
    
    try:
        # 列出所有表
        all_tables = list_all_tables(conn)
        
        # 搜索常见的表名模式
        search_patterns = ['2025-12_yc', 'yc', 'cf_', '2025']
        
        print("\n" + "="*80)
        print("🔎 表名模式搜索")
        print("="*80)
        
        for pattern in search_patterns:
            search_table_by_pattern(conn, pattern)
        
        # 检查配置中的表是否存在
        print("\n" + "="*80)
        print("⚙️  配置文件中的表验证")
        print("="*80)
        
        configured_tables = []
        if config.has_section('DETAIL_QUERY') and config.has_option('DETAIL_QUERY', 'table_name'):
            detail_table = config.get('DETAIL_QUERY', 'table_name')
            configured_tables.append(('DETAIL_QUERY', detail_table))
            
        if config.has_section('PATH_MATCH') and config.has_option('PATH_MATCH', 'table_name'):
            path_table = config.get('PATH_MATCH', 'table_name')
            configured_tables.append(('PATH_MATCH', path_table))
        
        for section, table_name in configured_tables:
            exists = table_name in all_tables
            status = "✅ 存在" if exists else "❌ 不存在"
            print(f"[{section}] 表名: {table_name} - {status}")
            
            if not exists and section == 'DETAIL_QUERY':
                print(f"\n   ⚠️  警告：详单查询配置的表不存在！")
                print(f"   这可能导致更新操作失败")
                
    finally:
        conn.close()
        print("\n🔒 数据库连接已关闭")

if __name__ == "__main__":
    main()
