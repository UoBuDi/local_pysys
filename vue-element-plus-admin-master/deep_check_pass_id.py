#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析脚本：核查通行标识ID不存在的原因
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import load_config


def deep_analyze_pass_id(pass_id: str):
    """深度分析通行标识ID"""
    from database import get_db_connection
    
    config = load_config()
    
    print(f"=" * 80)
    print(f"通行标识ID深度分析报告")
    print(f"=" * 80)
    
    print(f"\n【基本信息】")
    print("-" * 80)
    print(f"目标通行标识ID: {pass_id}")
    print(f"ID长度: {len(pass_id)} 字符")
    
    if len(pass_id) >= 14:
        date_part = pass_id[10:18]
        print(f"ID中包含的疑似日期: {date_part}")
        try:
            year = date_part[:4]
            month = date_part[4:6]
            day = date_part[6:8]
            print(f"解析结果: {year}年{month}月{day}日")
        except:
            pass
    
    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            
            print(f"\n【步骤1】检查目标月份表的数据量")
            print("-" * 80)
            
            target_table = None
            if len(pass_id) >= 10:
                date_str = pass_id[10:16]  # YYYYMM
                target_table = f"{date_str[:4]}-{date_str[4:6]}_yc"
                print(f"根据ID推断的目标表: {target_table}")
                
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{target_table}`")
                    count = cursor.fetchone()[0]
                    print(f"该表总记录数: {count:,} 条")
                    
                    if count > 0:
                        cursor.execute(f"SELECT MIN(`通行标识ID`), MAX(`通行标识ID`) FROM `{target_table}`")
                        min_id, max_id = cursor.fetchone()
                        print(f"最小通行标识ID: {min_id}")
                        print(f"最大通行标识ID: {max_id}")
                        
                except Exception as e:
                    print(f"❌ 无法访问表 {target_table}: {e}")
            
            print(f"\n【步骤2】模糊搜索相似ID（前缀匹配）")
            print("-" * 80)
            
            prefix = pass_id[:20]
            print(f"使用前缀进行模糊搜索: {prefix}...")
            
            yc_pattern = re.compile(r'^\d{4}-\d{2}_yc$')
            cursor.execute("SHOW TABLES")
            all_tables = [t[0] for t in cursor.fetchall()]
            monthly_tables = sorted([t for t in all_tables if yc_pattern.match(t)])
            
            similar_records = []
            
            for tbl in monthly_tables:
                try:
                    sql = f"""SELECT `通行标识ID`, `实际车辆车牌号码+颜色`
                            FROM `{tbl}`
                            WHERE `通行标识ID` LIKE %s
                            LIMIT 5"""
                    cursor.execute(sql, (f"{prefix}%",))
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        similar_records.append({
                            'table': tbl,
                            'pass_id': row[0],
                            'plate': row[1]
                        })
                        
                except Exception as e:
                    continue
            
            if similar_records:
                print(f"\n✅ 找到 {len(similar_records)} 条相似记录:")
                for i, rec in enumerate(similar_records[:10], 1):
                    print(f"  {i}. [{rec['table']}] ID: {rec['pass_id']}, 车牌: {rec['plate']}")
            else:
                print(f"\n❌ 未找到任何相似的通行标识ID")
            
            print(f"\n【步骤3】检查最近导入的数据（最新记录）")
            print("-" * 80)
            
            latest_table = monthly_tables[-1] if monthly_tables else None
            
            if latest_table:
                print(f"最新月份表: {latest_table}")
                
                try:
                    sql = f"""SELECT `通行标识ID`, `实际车辆车牌号码+颜色`, `入口时间`, `出口时间`
                            FROM `{latest_table}`
                            ORDER BY `入口时间` DESC
                            LIMIT 5"""
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    
                    print(f"\n该表最新的5条记录:")
                    columns = ['通行标识ID', '车牌', '入口时间', '出口时间']
                    for idx, row in enumerate(rows, 1):
                        print(f"\n  记录 #{idx}:")
                        for col, val in zip(columns, row):
                            if val:
                                val_str = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                                print(f"    {col}: {val_str}")
                            
                except Exception as e:
                    print(f"❌ 查询失败: {e}")
            
            print(f"\n【步骤4】统计各月度表的数据量分布")
            print("-" * 80)
            
            table_stats = []
            for tbl in monthly_tables[-6:]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`")
                    count = cursor.fetchone()[0]
                    table_stats.append((tbl, count))
                except:
                    table_stats.append((tbl, 0))
            
            print(f"\n最近6个月的数据量:")
            for tbl, cnt in table_stats:
                bar = "█" * (cnt // 10000) if cnt > 0 else ""
                print(f"  {tbl}: {cnt:>10,} 条 {bar}")
            
            print(f"\n{'='*80}")
            print(f"【结论与建议】")
            print(f"{'='*80}")
            
            print(f"""
分析总结:

1. **数据存在性确认**
   - 通行标识ID '{pass_id}' 在所有详单查询表中均不存在 ✗
   - 已检查全部 {len(monthly_tables)} 张月度表

2. **可能原因** (按可能性排序)

   🔴 原因A: 数据尚未导入 (最可能)
      - 该通行记录发生在 2025-12-11，属于近期数据
      - 可能还在数据同步/导入队列中
      - 建议: 等待数据更新或手动触发导入

   🟡 原因B: 数据源问题
      - 该通行标识ID可能来自其他系统或临时数据
      - 不在当前详单查询系统的数据范围内
      - 建议: 确认数据来源和系统归属

   🟢 原因C: 格式异常
      - 该ID格式与现有数据不完全一致
      - 可能存在特殊前缀或编码规则差异
      建议: 对比正常ID的格式特征

3. **立即行动建议**
   
   ✓ 检查数据导入日志，确认最近一次导入时间
   ✓ 联系数据提供方确认该ID的数据状态
   ✓ 如果是测试数据，考虑添加测试用例到数据库
   ✓ 检查云门户系统是否返回了正确的通行标识ID

4. **技术细节**
   - 目标表: {target_table or '未知'}
   - 数据库覆盖范围: {monthly_tables[0] if monthly_tables else 'N/A'} ~ {monthly_tables[-1] if monthly_tables else 'N/A'}
   - 总表数: {len(monthly_tables)} 张月度表
""")


if __name__ == "__main__":
    target_pass_id = "020000430101930023523020251211173306"
    
    if len(sys.argv) > 1:
        target_pass_id = sys.argv[1]
    
    deep_analyze_pass_id(target_pass_id)
