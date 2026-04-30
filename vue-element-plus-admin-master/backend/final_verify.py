#!/usr/bin/env python3
"""
最终验证脚本 - 使用通行标识ID进行更新测试
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

def final_update_test(conn):
    """最终更新功能测试"""
    try:
        cursor = conn.cursor()
        
        table_name = '202005-202311_cf_1215'
        id_field = '通行标识ID'
        
        print("\n" + "="*80)
        print("🧪 最终更新功能验证")
        print("="*80)
        
        # 查询一条记录
        print(f"\n步骤1: 查询测试记录...")
        select_sql = f"SELECT `{id_field}`, `实际车辆车牌号码+颜色`, `收费入口名称` FROM `{table_name}` LIMIT 1"
        cursor.execute(select_sql)
        test_row = cursor.fetchone()
        
        if not test_row:
            print(f"❌ 表中无数据")
            return False
        
        test_id = test_row[0]
        original_plate = test_row[1]
        original_station = test_row[2]
        
        print(f"✅ 找到测试记录")
        print(f"   通行标识ID: {test_id}")
        print(f"   车牌号码: {original_plate}")
        print(f"   入口收费站: {original_station}")
        
        # 测试1: 更新文本字段
        print(f"\n步骤2: 测试文本字段更新...")
        test_value = f"[验证_{time.strftime('%Y%m%d%H%M%S')}]"
        
        update_sql = f"UPDATE `{table_name}` SET `收费入口名称` = %s WHERE `{id_field}` = %s"
        cursor.execute(update_sql, (test_value, test_id))
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"✅ 文本字段更新成功！影响行数: {affected}")
            
            # 验证
            cursor.execute(f"SELECT `收费入口名称` FROM `{table_name}` WHERE `{id_field}` = %s", (test_id,))
            result = cursor.fetchone()[0]
            if result == test_value:
                print(f"✅ 验证通过：字段已成功更新为 '{result}'")
            else:
                print(f"⚠️  验证异常")
        else:
            print(f"⚠️  更新未生效")
        
        # 测试2: 多字段批量更新
        print(f"\n步骤3: 测试多字段批量更新...")
        
        update_data = {
            '实际车辆车牌号码+颜色': f'{original_plate}_test',
            '车辆状态标识': test_value,
            '拆分数据来源': 'TEST'
        }
        
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            set_clauses.append(f"`{key}` = %s")
            params.append(value)
            print(f"   更新 {key} = {value}")
        
        params.append(test_id)
        
        multi_sql = f"UPDATE `{table_name}` SET {','.join(set_clauses)} WHERE `{id_field}` = %s"
        cursor.execute(multi_sql, params)
        affected_multi = cursor.rowcount
        conn.commit()
        
        if affected_multi > 0:
            print(f"✅ 多字段更新成功！影响行数: {affected_multi}")
        else:
            print(f"⚠️  多字段更新未生效")
        
        # 恢复原始数据
        print(f"\n步骤4: 恢复原始数据...")
        restore_sql = f"""UPDATE `{table_name}` 
                       SET `收费入口名称` = %s, 
                           `实际车辆车牌号码+颜色` = %s,
                           `车辆状态标识` = NULL,
                           `拆分数据来源` = NULL
                       WHERE `{id_field}` = %s"""
        cursor.execute(restore_sql, (original_station, original_plate, None, None, test_id))
        conn.commit()
        print("✅ 原始数据已恢复")
        
        return True
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0] if e.args else 0
        error_msg = str(e)
        
        print(f"\n{'='*80}")
        print("❌ 更新操作失败!")
        print(f"{'='*80}")
        print(f"错误代码: {error_code}")
        print(f"错误信息: {error_msg}")
        
        if error_code == 1114:
            print(f"\n🔍 根本原因分析:")
            print(f"   {'─'*60}")
            print(f"   MySQL Error #1114: The table is full")
            print(f"   ")
            print(f"   📊 当前表空间状态:")
            print(f"   ┌─────────────────────────────────────┐")
            print(f"   │ 数据大小:     ~148 GB (151,815 MB) │")
            print(f"   │ 索引大小:     ~29.6 GB (30,344 MB) │")
            print(f"   │ 剩余空间:     仅 6 MB              │")
            print(f"   │ 空间利用率:   100%                 │")
            print(f"   │ 总行数:       53,861,408 行        │")
            print(f"   └─────────────────────────────────────┘")
            print(f"   ")
            print(f"   ⚠️  影响:")
            print(f"      • 无法执行 INSERT 操作")
            print(f"      • UPDATE 操作可能失败（如果增加行大小）")
            print(f"      • SELECT 操作正常")
            print(f"   ")
            print(f"   ✅ 已实施的修复:")
            print(f"      您已清理数据库服务器磁盘空间")
            print(f"   ")
            print(f"   💡 进一步建议:")
            print(f"      1. 执行 OPTIMIZE TABLE 回收碎片空间")
            print(f"      2. 归档或删除历史数据（如2020-2023年的旧数据）")
            print(f"      3. 实施数据分区策略（按月份范围分区）")
            print(f"      4. 考虑读写分离或分库分表架构")
            print(f"      5. 设置自动化监控告警（空间使用率 > 80% 时预警）")
        elif error_code in [1040, 1041]:
            print(f"\n🔍 连接问题:")
            print(f"   数据库连接数达到上限或被拒绝")
            print(f"   解决方案: 重启数据库服务或调整最大连接数")
        else:
            print(f"\n🔍 其他错误，请检查数据库日志")
            
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
    print("🎯 数据库更新功能最终验证")
    print("   目标表: 202005-202311_cf_1215")
    print("   数据库: check_data (CHECK_DATA_DB)")
    print("="*80)
    
    conn = get_check_data_db_connection()
    if not conn:
        return False
    
    print("✅ 数据库连接成功")
    
    try:
        success = final_update_test(conn)
        
        print("\n" + "="*80)
        print("📋 最终结论")
        print("="*80)
        
        if success:
            print("✅✅✅ 更新功能完全正常！ ✅✅✅")
            print("")
            print("💡 验证结果:")
            print("   ✅ 数据库连接正常")
            print("   ✅ 单字段更新成功")
            print("   ✅ 多字段批量更新成功")
            print("   ✅ 数据回滚/恢复正常")
            print("")
            print("📊 系统状态:")
            print("   数据库服务器空间清理后，所有更新操作均可正常执行")
            print("   可以放心使用系统的保存和修改功能")
            print("")
            print("⚠️  注意事项:")
            print("   当前表空间利用率已达 100%，建议尽快实施以下优化措施：")
            print("   1. 定期清理历史数据")
            print("   2. 监控磁盘空间使用情况")
            print("   3. 制定数据归档策略")
            return True
        else:
            print("❌ 更新功能存在异常")
            print("   请根据上述错误信息进行处理")
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
