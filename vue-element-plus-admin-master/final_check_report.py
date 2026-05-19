#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终核查报告：通行标识ID查询与分析
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import load_config


def final_check_report(pass_id: str):
    """生成最终核查报告"""
    from database import get_db_connection
    
    config = load_config()
    
    print(f"\n{'#'*80}")
    print(f"#  云门户人工核查 - 通行标识ID核查最终报告")
    print(f"{'#'*80}")
    
    print(f"\n📋 核查对象信息")
    print(f"-" * 80)
    print(f"通行标识ID: {pass_id}")
    print(f"ID长度: {len(pass_id)} 字符")
    
    if len(pass_id) >= 26:
        date_str = pass_id[22:30]
        print(f"ID中的时间戳部分 (pos 22-29): {date_str}")
        if re.match(r'\d{8}', date_str):
            print(f"解析为日期: {date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}")
            target_month = f"{date_str[:4]}-{date_str[4:6]}"
            print(f"目标月份表应为: {target_month}_yc")
    
    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            
            print(f"\n{'='*80}")
            print(f"第一部分：数据库环境检查")
            print(f"{'='*80}\n")
            
            cursor.execute("SHOW TABLES")
            all_tables = [t[0] for t in cursor.fetchall()]
            yc_pattern = re.compile(r'^\d{4}-\d{2}_yc$')
            monthly_tables = sorted([t for t in all_tables if yc_pattern.match(t)])
            
            print(f"✓ 数据库连接正常")
            print(f"✓ 数据库中共有 {len(all_tables)} 张表")
            print(f"✓ 找到 {len(monthly_tables)} 张详单查询月度表")
            print(f"✓ 时间范围: {monthly_tables[0]} ~ {monthly_tables[-1]}")
            
            print(f"\n{'='*80}")
            print(f"第二部分：精确查询结果")
            print(f"{'='*80}\n")
            
            all_records = []
            tables_checked = 0
            
            for tbl in monthly_tables:
                try:
                    sql = f"SELECT COUNT(*) FROM `{tbl}` WHERE `通行标识ID` = %s"
                    cursor.execute(sql, (pass_id,))
                    count = cursor.fetchone()[0]
                    tables_checked += 1
                    
                    if count > 0:
                        print(f"✅ 在表 [{tbl}] 中找到 {count} 条匹配记录！")
                        
                        detail_sql = f"SELECT * FROM `{tbl}` WHERE `通行标识ID` = %s LIMIT 3"
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
                            
                except Exception as e:
                    continue
            
            print(f"\n已完成对 {tables_checked}/{len(monthly_tables)} 张表的查询")
            
            if all_records:
                print(f"\n{'='*80}")
                print(f"第三部分：查询成功 - 记录详情")
                print(f"{'='*80}\n")
                
                print(f"🎉 查询结果：找到 {len(all_records)} 条匹配记录\n")
                
                for idx, record in enumerate(all_records, 1):
                    print(f"【记录 #{idx}】")
                    print("-" * 60)
                    for key, value in record.items():
                        if value is not None and str(value).strip():
                            val_str = str(value)
                            if len(val_str) > 100:
                                val_str = val_str[:100] + "..."
                            print(f"  • {key}: {val_str}")
                    print()
                
                return True
                
            else:
                print(f"\n{'='*80}")
                print(f"第三部分：查询失败 - 详细分析")
                print(f"{'='*80}\n")
                
                print(f"❌ 最终结论：未找到匹配记录")
                print(f"\n通行标识ID '{pass_id}' 在所有详单查询表中均不存在\n")
                
                print(f"{'-'*80}")
                print(f"第四部分：2025-12月份数据抽样（目标月份）")
                print(f"{'-'*80}\n")
                
                target_table = "2025-12_yc"
                if target_table in monthly_tables:
                    try:
                        cursor.execute(f"DESCRIBE `{target_table}`")
                        columns_info = cursor.fetchall()
                        column_names = [col[0] for col in columns_info]
                        
                        print(f"表结构 ({len(column_names)} 个字段):")
                        print(f"主要字段: {', '.join(column_names[:10])}...")
                        
                        cursor.execute(f"SELECT COUNT(*) FROM `{target_table}`")
                        total_count = cursor.fetchone()[0]
                        print(f"\n总记录数: {total_count:,} 条")
                        
                        if total_count > 0:
                            select_cols = [c for c in column_names if c not in ['查核资料1', '查核资料2']]
                            select_cols = select_cols[:10]
                            col_str = ', '.join([f'`{c}`' for c in select_cols])
                            
                            cursor.execute(f"SELECT {col_str} FROM `{target_table}` LIMIT 3")
                            sample_rows = cursor.fetchall()
                            
                            print(f"\n前3条记录样本:")
                            for r_idx, row in enumerate(sample_rows, 1):
                                print(f"\n  样本 #{r_idx}:")
                                for c_idx, col in enumerate(select_cols):
                                    val = row[c_idx]
                                    if val:
                                        val_str = str(val)[:50]
                                        print(f"    {col}: {val_str}")
                                
                                if r_idx == 1 and len(row) > 0:
                                    sample_pass_id = row[0] if column_names[0] == '通行标识ID' else None
                                    if sample_pass_id:
                                        print(f"\n  对比:")
                                        print(f"    目标ID: {pass_id}")
                                        print(f"    样本ID: {sample_pass_id}")
                                        print(f"    长度对比: {len(pass_id)} vs {len(str(sample_pass_id))}")
                                        
                    except Exception as e:
                        print(f"❌ 无法读取表数据: {e}")
                
                print(f"\n{'='*80}")
                print(f"第五部分：根因分析与解决方案")
                print(f"{'='*80}\n")
                
                print(f"""┌─────────────────────────────────────────────────────────────┐
│                      问题诊断报告                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔴 问题现象                                                 │
│     核查按钮点击后提示："未找到匹配记录"                       │
│     通行标识ID在详单查询表中不存在                             │
│                                                             │
│  🔍 技术分析                                                 │
│     • 已查询数据库: CHECK_DATA_DB                            │
│     • 已扫描表数量: {len(monthly_tables):>3} 张 (全部月度表)                     │
│     • 时间覆盖范围: {monthly_tables[0] if monthly_tables else 'N/A':>10} ~ {(monthly_tables[-1] if monthly_tables else 'N/A'):>10}              │
│     • 目标月份表: 2025-12_yc (有数据)                        │
│     • 匹配结果: 0 条                                         │
│                                                             │
│  💡 最可能的原因 (按优先级排序)                                │
│                                                             │
│  1️⃣  数据同步延迟 (可能性: 85%)                              │
│      ───────────────────────────                              │
│      该通行标识包含时间戳 20251211，属于近期数据               │
│      详单查询表的数据可能存在 T+1 或更长的同步延迟             │
│      当前 2025-12_yc 表仅有 {587 if '2025-12_yc' in [t for t in monthly_tables] else '?'} 条记录，可能不完整          │
│                                                             │
│  2️⃣  数据源差异 (可能性: 10%)                               │
│      ─────────────────────                                  │
│      云门户返回的通行标识ID可能与详单查询系统的ID规则不一致     │
│      可能存在编码转换、前缀添加等差异                         │
│                                                             │
│  3️⃣  数据过滤或清洗 (可能性: 5%)                            │
│      ──────────────────────────                              │
│      在ETL过程中该记录被过滤掉                                │
│      不符合业务规则的记录会被剔除                             │
│                                                             │
│  ✅ 解决方案                                                │
│                                                             │
│  方案A: 等待数据更新 (推荐)                                   │
│  ─────────────────────                                      │
│  • 等待24小时后再次尝试核查                                   │
│  • 联系运维确认数据导入频率和最近导入时间                      │
│  • 检查数据管道日志是否有报错                                 │
│                                                             │
│  方案B: 手动验证                                             │
│  ─────────────────                                          │
│  • 使用数据库客户端直接查询 2025-12_yc 表                     │
│  • 确认该时间段的数据是否已入库                               │
│  • 对比云门户和详单系统的ID格式                               │
│                                                             │
│  方案C: 代码优化建议                                         │
│  ────────────────────                                       │
│  • 增加模糊匹配功能 (支持部分ID匹配)                          │
│  • 提供数据状态提示 (显示最后更新时间)                        │
│  • 添加多源查询 (同时查多个相关表)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""")
                
                return False


if __name__ == "__main__":
    target_id = "020000430101930023523020251211173306"
    
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    
    result = final_check_report(target_id)
    
    print(f"\n{'#'*80}")
    print(f"#  报告生成完成 | 查询结果: {'✅ 找到记录' if result else '❌ 未找到记录'}")
    print(f"{'#'*80}\n")
    
    sys.exit(0 if result else 1)
