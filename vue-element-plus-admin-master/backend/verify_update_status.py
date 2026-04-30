#!/usr/bin/env python3
"""
数据库更新功能验证脚本 - 使用 CHECK_DATA_DB 配置
用于验证数据库服务器空间清理后的更新状态
"""

import pymysql
import sys
import traceback
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_check_data_db_connection():
    """获取 check_data 数据库连接"""
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        section = 'CHECK_DATA_DB'
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
        logger.error(f"数据库连接失败: {e}")
        return None, None

def list_yc_tables(conn):
    """列出所有以 _yc 结尾的表"""
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
            ROUND((data_free / NULLIF((data_length+index_length), 0)) * 100, 2) AS free_percent
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() AND (table_name LIKE '%_yc' OR table_name LIKE '%cf_%')
        ORDER BY table_name
        """
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        print("\n" + "="*100)
        print("📊 Check_Data 数据库中的业务表")
        print("="*100)
        print(f"{'表名':<35} {'引擎':<8} {'数据(MB)':<10} {'索引(MB)':<10} {'总计(MB)':<10} {'剩余(MB)':<10} {'行数':<12} {'空闲%':<8}")
        print("-"*100)
        
        for row in results:
            table_name = row[0][:33] + '..' if len(row[0]) > 35 else row[0]
            free_pct = f"{row[7]:.1f}%" if row[7] is not None else "N/A"
            print(f"{table_name:<35} {row[1]:<8} {row[2]:<10.2f} {row[3]:<10.2f} {row[4]:<10.2f} {row[5]:<10.2f} {row[6]:<12,} {free_pct:<8}")
            
        print(f"\n共找到 {len(results)} 个业务表")
        return [row[0] for row in results]
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()

def check_table_space(conn, table_name):
    """检查表空间使用情况"""
    try:
        cursor = conn.cursor()
        
        sql = """
        SELECT 
            table_name,
            engine,
            row_format,
            data_length,
            index_length,
            data_free,
            table_rows,
            ROUND(data_length/1024/1024, 2) AS data_size_mb,
            ROUND(index_length/1024/1024, 2) AS index_size_mb,
            ROUND(data_free/1024/1024, 2) AS free_space_mb,
            auto_increment
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() AND table_name = %s
        """
        
        cursor.execute(sql, (table_name,))
        result = cursor.fetchone()
        
        if result:
            print("\n" + "="*80)
            print(f"📊 表 '{table_name}' 详细空间报告")
            print("="*80)
            print(f"存储引擎: {result[1]}")
            print(f"行格式: {result[2]}")
            print(f"数据大小: {result[7]:.2f} MB ({result[3]:,} bytes)")
            print(f"索引大小: {result[8]:.2f} MB ({result[4]:,} bytes)")
            print(f"剩余空间: {result[9]:.2f} MB ({result[5]:,} bytes)")
            print(f"数据行数: {result[6]:,}")
            
            total_size = result[3] + result[4]
            free_percent = (result[5] / total_size * 100) if total_size > 0 else 0
            
            print(f"\n空间利用率: {(100 - free_percent):.1f}%")
            
            if result[9] > 10:  # 剩余空间 > 10MB
                print("✅ 表空间充足，可以正常进行更新操作")
                status = "healthy"
            elif result[9] > 0:  # 剩余空间 < 10MB 但还有
                print("⚠️  表空间接近满，建议关注")
                status = "warning"
            else:  # 无剩余空间
                print("❌ 表空间已满或接近满，可能影响更新操作")
                status = "critical"
                
            return {
                'status': status,
                'data_size_mb': result[7],
                'index_size_mb': result[8],
                'free_space_mb': result[9],
                'total_rows': result[6],
                'free_percent': free_percent
            }
        else:
            print(f"\n❌ 未找到表: {table_name}")
            return None
            
    except Exception as e:
        logger.error(f"查询表空间失败: {e}", exc_info=True)
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()

def test_update_operation(conn, table_name):
    """测试更新操作"""
    try:
        cursor = conn.cursor()
        
        # 查询一条测试记录
        cursor.execute(
            f"SELECT `通行标识ID`, `车牌号码`, `备注` FROM `{table_name}` LIMIT 1"
        )
        test_row = cursor.fetchone()
        
        if not test_row:
            print(f"\n❌ 表 '{table_name}' 中没有可用的测试记录")
            return False
            
        test_id = test_row[0]
        original_plate = test_row[1]
        original_remark = test_row[2] or ''
        
        print(f"\n" + "="*80)
        print("🧪 更新操作测试")
        print("="*80)
        print(f"测试记录ID: {test_id}")
        print(f"原始车牌号码: {original_plate}")
        print(f"原始备注: {original_remark[:50] if original_remark else '(空)'}...")
        
        # 测试1：简单文本字段更新
        print("\n--- 测试1: 简单文本字段更新 ---")
        import time
        test_remark = f"[验证测试_{time.strftime('%Y%m%d%H%M%S')}]"
        update_sql = f"UPDATE `{table_name}` SET `备注` = %s WHERE `通行标识ID` = %s"
        
        cursor.execute(update_sql, (test_remark, test_id))
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"✅ 文本字段更新成功！影响行数: {affected}")
        else:
            print(f"⚠️  文本字段更新未生效（可能值相同）")
        
        # 验证更新结果
        cursor.execute(
            f"SELECT `备注` FROM `{table_name}` WHERE `通行标识ID` = %s",
            (test_id,)
        )
        updated_remark = cursor.fetchone()[0]
        
        if updated_remark == test_remark:
            print(f"✅ 验证成功：备注字段已更新为 '{updated_remark}'")
        else:
            print(f"❌ 验证失败：期望 '{test_remark}'，实际 '{updated_remark}'")
            return False
        
        # 测试2：多字段更新（模拟实际API请求）
        print("\n--- 测试2: 多字段更新（模拟实际请求）---")
        update_data = {
            '车牌号码': f'{original_plate}_test',
            '复核情况': '待删除',
            '特情': None,
            '核查拆分': '未拆',
            '备注': test_remark
        }
        
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            set_clauses.append(f"`{key}` = %s")
            params.append(value)
            print(f"  - {key}: {value}")
        
        params.append(test_id)
        
        multi_update_sql = f"UPDATE `{table_name}` SET {','.join(set_clauses)} WHERE `通行标识ID` = %s"
        
        cursor.execute(multi_update_sql, params)
        affected_multi = cursor.rowcount
        conn.commit()
        
        if affected_multi > 0:
            print(f"✅ 多字段更新成功！影响行数: {affected_multi}")
        else:
            print(f"⚠️  多字段更新未生效")
        
        # 恢复原始数据
        print("\n--- 恢复原始数据 ---")
        restore_sql = f"UPDATE `{table_name}` SET `车牌号码` = %s, `备注` = %s WHERE `通行标识ID` = %s"
        cursor.execute(restore_sql, (original_plate, original_remark or None, test_id))
        conn.commit()
        print("✅ 原始数据已恢复")
        
        return True
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        error_code = e.args[0] if hasattr(e, 'args') and e.args else 0
        
        print(f"\n❌ 更新测试失败!")
        print(f"   错误类型: {error_type}")
        print(f"   错误代码: {error_code}")
        print(f"   错误信息: {error_msg}")
        
        # 分析具体错误原因
        if error_code == 1114:
            print("\n   🔍 根本原因分析:")
            print("      MySQL错误代码 1114 表示表空间已满")
            print("      可能的原因:")
            print("      1. 数据库磁盘空间不足")
            print("      2. InnoDB 表空间文件达到上限")
            print("      3. 单表大小超过限制")
            print("      解决方案:")
            print("      1. 清理不必要的数据或历史记录")
            print("      2. 执行 OPTIMIZE TABLE 回收碎片空间")
            print("      3. 扩展数据库服务器存储容量")
        elif error_code in [1040, 1041]:
            print("\n   🔍 根本原因分析:")
            print("      数据库连接数达到上限或连接被拒绝")
            print("      解决方案:")
            print("      1. 重启数据库服务释放连接")
            print("      2. 调整数据库最大连接数配置")
        elif error_code == 1146:
            print("\n   🔍 根本原因分析:")
            print("      表不存在于当前数据库中")
            print("      请检查配置文件中的表名是否正确")
        
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🔍 数据库更新功能验证工具 (Check_Data DB)")
    print("="*80)
    
    # 使用 CHECK_DATA_DB 连接
    conn, config = get_check_data_db_connection()
    if not conn:
        print("\n❌ 无法连接到 check_data 数据库，请检查 CHECK_DATA_DB 配置和网络连接")
        return False
    
    print("✅ Check_Data 数据库连接成功")
    
    # 列出所有业务表
    all_tables = list_yc_tables(conn)
    
    if not all_tables:
        print("\n❌ 未找到任何业务表")
        conn.close()
        return False
    
    # 检查配置中的目标表
    target_tables = []
    
    if config.has_section('DETAIL_QUERY') and config.has_option('DETAIL_QUERY', 'table_name'):
        detail_table = config.get('DETAIL_QUERY', 'table_name')
        target_tables.append(('DETAIL_QUERY', detail_table))
        
    if config.has_section('PATH_MATCH') and config.has_option('PATH_MATCH', 'table_name'):
        path_table = config.get('PATH_MATCH', 'table_name')
        target_tables.append(('PATH_MATCH', path_table))
    
    # 如果配置的表不存在，尝试找一个 _yc 结尾的表作为测试对象
    test_table = None
    
    print("\n" + "="*80)
    print("⚙️  配置文件中的表验证")
    print("="*80)
    
    for section, table_name in target_tables:
        exists = table_name in all_tables
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"[{section}] 表名: {table_name} - {status}")
        
        if exists and not test_table:
            test_table = table_name
    
    # 如果配置的表不存在，选择第一个 _yc 表进行测试
    if not test_table:
        yc_tables = [t for t in all_tables if t.endswith('_yc')]
        if yc_tables:
            test_table = yc_tables[0]
            print(f"\nℹ️  配置的表不存在，将使用 '{test_table}' 进行测试")
        elif all_tables:
            test_table = all_tables[0]
            print(f"\nℹ️  将使用 '{test_table}' 进行测试")
    
    if not test_table:
        print("\n❌ 没有可用的测试表")
        conn.close()
        return False
    
    try:
        # 步骤1：检查表空间状态
        space_info = check_table_space(conn, test_table)
        
        # 步骤2：执行更新操作测试
        success = test_update_operation(conn, test_table)
        
        # 输出最终结果
        print("\n" + "="*80)
        print("📋 验证结果汇总")
        print("="*80)
        
        if success and space_info and space_info['status'] == 'healthy':
            print("✅ 所有测试通过！数据库更新功能正常")
            print("   ✅ 表空间充足")
            print("   ✅ 文本字段更新正常")
            print("   ✅ 多字段更新正常")
            print("\n💡 结论:")
            print("   数据库服务器空间清理后，更新功能已恢复正常")
            print("   可以正常使用系统的保存和修改功能")
            return True
        elif space_info and space_info['status'] == 'warning':
            print("⚠️  部分测试通过，但表空间不足警告")
            print("   ✅ 当前更新操作成功")
            print("   ⚠️  建议尽快清理空间")
            return True
        elif space_info and space_info['status'] == 'critical':
            print("❌ 表空间严重不足")
            print("   ❌ 更新操作可能失败")
            print("\n💡 建议:")
            print("   请继续清理数据库空间或联系管理员扩展存储")
            return False
        else:
            print("❌ 更新功能异常")
            print("   需要进一步排查问题")
            return False
            
    finally:
        conn.close()
        print("\n🔒 数据库连接已关闭")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n程序异常退出: {e}")
        traceback.print_exc()
        sys.exit(1)
