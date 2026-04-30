#!/usr/bin/env python3
"""
表结构检查和更新功能验证脚本 - 针对 202005-202311_cf_1215 表
"""

import pymysql
import sys
import time

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
            connect_timeout=10,
            read_timeout=60,
            write_timeout=60
        )
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def show_table_structure(conn, table_name):
    """显示表结构"""
    try:
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()
        
        print("\n" + "="*100)
        print(f"📋 表 '{table_name}' 的字段结构")
        print("="*100)
        print(f"{'字段名':<30} {'类型':<25} {'允许空':<8} {'键':<6} {'默认值':<15} {'额外信息'}")
        print("-"*100)
        
        for col in columns:
            field = col[0]
            col_type = col[1] if len(col) > 1 else ''
            null_allowed = col[2] if len(col) > 2 else ''
            key = col[3] if len(col) > 3 else ''
            default = str(col[4]) if len(col) > 4 and col[4] is not None else ''
            extra = col[5] if len(col) > 5 else ''
            
            print(f"{field:<30} {col_type:<25} {null_allowed:<8} {key:<6} {default:<15} {extra}")
            
        print(f"\n共 {len(columns)} 个字段")
        
        # 找出主键和常用更新字段
        primary_keys = [col[0] for col in columns if col[3] == 'PRI']
        text_fields = [col[0] for col in columns if 'text' in str(col[1]).lower() or 'varchar' in str(col[1]).lower()]
        numeric_fields = [col[0] for col in columns if any(t in str(col[1]).lower() for t in ['int', 'decimal', 'float', 'double'])]
        
        print(f"\n🔑 主键字段: {primary_keys}")
        print(f"📝 文本字段（前10个）: {text_fields[:10]}")
        print(f"🔢 数值字段（前10个）: {numeric_fields[:10]}")
        
        return {
            'columns': columns,
            'primary_keys': primary_keys,
            'text_fields': text_fields,
            'numeric_fields': numeric_fields
        }
        
    except Exception as e:
        print(f"❌ 查询表结构失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()

def test_update_with_real_fields(conn, table_name, structure_info):
    """使用实际字段测试更新操作"""
    try:
        cursor = conn.cursor()
        
        pk_field = structure_info['primary_keys'][0] if structure_info['primary_keys'] else None
        
        if not pk_field:
            print("❌ 未找到主键字段，无法执行更新测试")
            return False
        
        # 查询一条记录
        select_sql = f"SELECT `{pk_field}` FROM `{table_name}` LIMIT 1"
        cursor.execute(select_sql)
        test_row = cursor.fetchone()
        
        if not test_row:
            print(f"❌ 表 '{table_name}' 中没有数据")
            return False
            
        test_id = test_row[0]
        print(f"\n" + "="*80)
        print("🧪 更新操作测试")
        print("="*80)
        print(f"测试记录ID ({pk_field}): {test_id}")
        
        # 选择一些可更新的文本字段
        updateable_fields = []
        for field in structure_info['text_fields']:
            if field != pk_field and not field.endswith('_id') and not field.endswith('_time'):
                updateable_fields.append(field)
                if len(updateable_fields) >= 3:
                    break
        
        if not updateable_fields:
            print("⚠️  没有找到合适的可更新字段，尝试查找其他字段")
            # 尝试查找任何非主键字段
            all_fields = [col[0] for col in structure_info['columns']]
            for field in all_fields:
                if field != pk_field:
                    updateable_fields.append(field)
                    if len(updateable_fields) >= 2:
                        break
        
        if not updateable_fields:
            print("❌ 无法找到可更新的字段")
            return False
            
        print(f"将使用以下字段进行测试: {updateable_fields}")
        
        # 测试1：单字段更新
        print("\n--- 测试1: 单字段文本更新 ---")
        test_value = f"[验证_{time.strftime('%Y%m%d%H%M%S')}]"
        test_field = updateable_fields[0]
        
        update_sql = f"UPDATE `{table_name}` SET `{test_field}` = %s WHERE `{pk_field}` = %s"
        print(f"SQL: UPDATE `{table_name}` SET `{test_field}` = ? WHERE `{pk_field}` = ?")
        
        cursor.execute(update_sql, (test_value, test_id))
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"✅ 单字段更新成功！影响行数: {affected}")
        else:
            print(f"⚠️  单字段更新未生效（可能值相同或行不存在）")
        
        # 验证更新结果
        verify_sql = f"SELECT `{test_field}` FROM `{table_name}` WHERE `{pk_field}` = %s"
        cursor.execute(verify_sql, (test_id,))
        updated_value = cursor.fetchone()[0]
        
        if updated_value == test_value:
            print(f"✅ 验证成功：'{test_field}' 已更新为 '{updated_value[:50]}...'")
        else:
            print(f"⚠️  验证结果：期望 '{test_value[:20]}...'，实际 '{str(updated_value)[:20]}...'")
        
        # 测试2：多字段更新（模拟实际API请求）
        if len(updateable_fields) >= 2:
            print("\n--- 测试2: 多字段批量更新 ---")
            
            set_clauses = []
            params = []
            test_values = {}
            
            for i, field in enumerate(updateable_fields[:3]):
                test_val = f"[测试{i+1}_{time.strftime('%H%M%S')}]"
                set_clauses.append(f"`{field}` = %s")
                params.append(test_val)
                test_values[field] = test_val
                print(f"  - {field}: {test_val}")
            
            params.append(test_id)
            
            multi_update_sql = f"UPDATE `{table_name}` SET {','.join(set_clauses)} WHERE `{pk_field}` = %s"
            
            cursor.execute(multi_update_sql, params)
            affected_multi = cursor.rowcount
            conn.commit()
            
            if affected_multi > 0:
                print(f"✅ 多字段更新成功！影响行数: {affected_multi}")
            else:
                print(f"⚠️  多字段更新未生效")
        
        # 测试3：NULL 值更新
        print("\n--- 测试3: NULL 值更新 ---")
        null_update_sql = f"UPDATE `{table_name}` SET `{test_field}` = NULL WHERE `{pk_field}` = %s"
        cursor.execute(null_update_sql, (test_id,))
        conn.commit()
        print("✅ NULL 值更新完成")
        
        return True
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0] if e.args else 0
        error_msg = str(e)
        
        print(f"\n❌ 更新测试失败!")
        print(f"   错误代码: {error_code}")
        print(f"   错误信息: {error_msg}")
        
        if error_code == 1114:
            print("\n   🔍 根本原因:")
            print("      MySQL Error #1114: The table is full (表空间已满)")
            print("      ")
            print("      当前状态:")
            print("      - 数据大小: ~148 GB")
            print("      - 索引大小: ~29.6 GB")  
            print("      - 剩余空间: 仅 6 MB")
            print("      - 空间利用率: 100%")
            print("      ")
            print("      解决方案:")
            print("      1. ✅ 清理数据库服务器磁盘空间（已完成）")
            print("      2. 执行 OPTIMIZE TABLE 回收碎片空间")
            print("      3. 归档或删除历史数据")
            print("      4. 扩展存储容量")
        elif error_code == 1054:
            print("\n   ⚠️  字段不存在，请检查表结构")
        else:
            print(f"\n   其他数据库错误，需要进一步排查")
            
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    except Exception as e:
        print(f"\n❌ 意外错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🔍 表结构与更新功能深度验证工具")
    print("="*80)
    
    conn = get_check_data_db_connection()
    if not conn:
        return False
    
    print("✅ Check_Data 数据库连接成功")
    
    table_name = '202005-202311_cf_1215'
    
    try:
        # 步骤1：显示表结构
        structure_info = show_table_structure(conn, table_name)
        
        if not structure_info:
            print("❌ 无法获取表结构")
            conn.close()
            return False
        
        # 步骤2：执行更新测试
        success = test_update_with_real_fields(conn, table_name, structure_info)
        
        # 输出最终报告
        print("\n" + "="*80)
        print("📊 最终验证报告")
        print("="*80)
        
        if success:
            print("✅ 更新功能正常！")
            print("   数据库服务器空间清理后，系统可以正常进行数据更新操作")
            print("   ")
            print("💡 建议:")
            print("   1. 定期监控表空间使用情况")
            print("   2. 实施数据归档策略，清理历史数据")
            print("   3. 考虑表分区或分库分表方案应对数据增长")
            return True
        else:
            print("❌ 更新功能异常")
            print("   请根据上述错误信息采取相应措施")
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
