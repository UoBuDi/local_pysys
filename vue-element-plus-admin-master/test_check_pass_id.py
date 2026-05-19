#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核查通行标识ID查询脚本
用于检查指定通行标识ID在详单查询表中是否存在
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import load_config


def query_pass_id(pass_id: str):
    """查询通行标识ID是否存在"""
    from database import get_db_connection

    config = load_config()
    
    print(f"=" * 80)
    print(f"通行标识ID核查报告")
    print(f"=" * 80)
    print(f"\n查询目标: {pass_id}")
    print(f"\n{'='*80}")
    
    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            print("\n【步骤1】获取数据库中的所有表")
            print("-" * 80)
            cursor.execute("SHOW TABLES")
            all_tables = [t[0] for t in cursor.fetchall()]
            print(f"数据库中共有 {len(all_tables)} 张表")
            
            print("\n【步骤2】筛选详单查询月度表（格式：YYYY-MM_yc）")
            print("-" * 80)
            yc_pattern = re.compile(r'^\d{4}-\d{2}_yc$')
            monthly_tables = sorted([t for t in all_tables if yc_pattern.match(t)])
            
            if not monthly_tables:
                print("⚠️  未找到任何详单查询月度表！")
                return
            
            print(f"找到 {len(monthly_tables)} 张月度详单表:")
            for i, tbl in enumerate(monthly_tables, 1):
                print(f"  {i:2d}. {tbl}")
            
            print(f"\n{'='*80}")
            print(f"【步骤3】在各月度表中查询通行标识ID: {pass_id}")
            print(f"{'='*80}\n")
            
            all_records = []
            found_tables = []
            
            for tbl in monthly_tables:
                try:
                    sql = f"SELECT COUNT(*) FROM `{tbl}` WHERE `通行标识ID` = %s"
                    cursor.execute(sql, (pass_id,))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        found_tables.append((tbl, count))
                        print(f"✅ 表 [{tbl}] 找到 {count} 条匹配记录")
                        
                        if len(all_records) < 10:
                            detail_sql = f"""SELECT 
                                `通行标识ID`,
                                `实际车辆车牌号码+颜色`,
                                `收费入口名称`,
                                `收费出口名称`,
                                `收费车型`,
                                `通行介质`,
                                `入口时间`,
                                `出口时间`
                            FROM `{tbl}` WHERE `通行标识ID` = %s LIMIT 5"""
                            
                            cursor.execute(detail_sql, (pass_id,))
                            columns = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            
                            for row in rows:
                                row_dict = {}
                                for i, col in enumerate(columns):
                                    val = row[i]
                                    if isinstance(val, bytes):
                                        try:
                                            val = val.decode('utf-8')
                                        except UnicodeDecodeError:
                                            val = val.hex()
                                    row_dict[col] = val
                                all_records.append(row_dict)
                    else:
                        pass
                    
                except Exception as e:
                    print(f"❌ 查询表 [{tbl}] 失败: {e}")
                    continue
            
            print(f"\n{'='*80}")
            print(f"【查询结果汇总】")
            print(f"{'='*80}")
            
            if all_records:
                print(f"\n✅ 核查结果：找到匹配记录！")
                print(f"   总计: {len(all_records)} 条记录 (最多显示前10条)")
                print(f"   分布在 {len(found_tables)} 张表中:")
                
                for tbl, cnt in found_tables:
                    print(f"     • {tbl}: {cnt} 条")
                
                print(f"\n【记录详情】")
                print("-" * 80)
                
                for idx, record in enumerate(all_records, 1):
                    print(f"\n📋 记录 #{idx}:")
                    for key, value in record.items():
                        if value:
                            print(f"   {key}: {value}")
                
                return True
                
            else:
                print(f"\n❌ 核查结果：未找到匹配记录")
                print(f"   通行标识ID '{pass_id}' 在所有 {len(monthly_tables)} 张详单查询表中均不存在\n")
                
                print(f"【可能原因分析】")
                print("-" * 80)
                print(f"1. 数据尚未导入到详单查询表")
                print(f"2. 通行标识ID输入错误或格式不正确")
                print(f"3. 该通行记录不在当前数据库覆盖的时间范围内")
                print(f"4. 数据同步延迟，最新数据还未入库")
                
                return False


if __name__ == "__main__":
    target_pass_id = "020000430101930023523020251211173306"
    
    if len(sys.argv) > 1:
        target_pass_id = sys.argv[1]
    
    result = query_pass_id(target_pass_id)
    
    sys.exit(0 if result else 1)
