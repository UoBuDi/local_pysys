#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确核查脚本：在配置文件指定的详单表中查询通行标识ID
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import load_config


def query_in_configured_table(pass_id: str):
    """在config.ini配置的DETAIL_QUERY表中查询"""
    from database import get_db_connection
    
    config = load_config()
    
    print("=" * 80)
    print("✅ 正确的核查方式：使用配置文件指定的表")
    print("=" * 80)
    
    # 读取配置
    table_name = config.get('DETAIL_QUERY', 'table_name', fallback='')
    
    print(f"\n【配置信息】")
    print("-" * 80)
    print(f"配置节: [DETAIL_QUERY]")
    print(f"配置表名: {table_name}")
    
    if not table_name:
        print("\n❌ 错误：未配置表名！请检查 config.ini 的 [DETAIL_QUERY] 节")
        return None
    
    print(f"\n【开始查询】")
    print("-" * 80)
    print(f"目标通行标识ID: {pass_id}")
    print(f"查询表: {table_name}")
    
    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            # 检查表是否存在
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                total_count = cursor.fetchone()[0]
                print(f"\n✅ 表 [{table_name}] 存在，总记录数: {total_count:,} 条")
                
            except Exception as e:
                print(f"\n❌ 表 [{table_name}] 不存在或无法访问: {e}")
                return None
            
            # 执行精确查询
            print(f"\n正在执行精确查询...")
            
            sql = f"""SELECT 
                `通行标识ID`,
                `实际车辆车牌号码+颜色`,
                `收费入口名称`,
                `收费出口名称`,
                `收费车型`,
                `通行介质`,
                `入口时间`,
                `出口时间`
            FROM `{table_name}`
            WHERE `通行标识ID` = %s
            LIMIT 10"""
            
            cursor.execute(sql, (pass_id,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            if rows:
                print(f"\n{'='*80}")
                print(f"🎉 查询成功：找到 {len(rows)} 条匹配记录！")
                print(f"{'='*80}\n")
                
                all_records = []
                for idx, row in enumerate(rows, 1):
                    record = {}
                    print(f"【记录 #{idx}】")
                    print("-" * 60)
                    for i, col in enumerate(columns):
                        val = row[i]
                        if isinstance(val, bytes):
                            try:
                                val = val.decode('utf-8')
                            except UnicodeDecodeError:
                                val = val.hex()
                        record[col] = val
                        if val is not None and str(val).strip():
                            val_str = str(val)
                            if len(val_str) > 80:
                                val_str = val_str[:80] + "..."
                            print(f"  • {col}: {val_str}")
                    all_records.append(record)
                    print()
                
                return {
                    'exists': True,
                    'match_count': len(rows),
                    'records': all_records,
                    'table_name': table_name
                }
                
            else:
                print(f"\n{'='*80}")
                print(f"❌ 查询结果：未找到匹配记录")
                print(f"{'='*80}\n")
                print(f"通行标识ID '{pass_id}' 在表 [{table_name}] 中不存在\n")
                
                # 显示表的样本数据，帮助用户了解数据格式
                print(f"【表样本数据】（前3条）")
                print("-" * 80)
                
                try:
                    sample_sql = f"SELECT * FROM `{table_name}` LIMIT 3"
                    cursor.execute(sample_sql)
                    sample_columns = [desc[0] for desc in cursor.description]
                    sample_rows = cursor.fetchall()
                    
                    for r_idx, row in enumerate(sample_rows, 1):
                        print(f"\n  样本记录 #{r_idx}:")
                        for c_idx, col in enumerate(sample_columns):
                            val = row[c_idx]
                            if val is not None and str(val).strip():
                                val_str = str(val)[:50]
                                if col == '通行标识ID':
                                    print(f"    ⭐ {col}: {val_str} (长度:{len(str(val))})")
                                else:
                                    print(f"    • {col}: {val_str}")
                                
                except Exception as e:
                    print(f"  无法获取样本数据: {e}")
                
                return {
                    'exists': False,
                    'match_count': 0,
                    'records': [],
                    'table_name': table_name
                }


if __name__ == "__main__":
    target_id = "020000430101930023523020251211173306"
    
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    
    result = query_in_configured_table(target_id)
    
    if result:
        print(f"\n{'#'*80}")
        if result['exists']:
            print(f"# ✅ 核查完成 | 在表 [{result['table_name']}] 中找到 {result['match_count']} 条记录")
        else:
            print(f"# ❌ 核查完成 | 在表 [{result['table_name']}] 中未找到记录")
        print(f"{'#'*80}\n")
        
        sys.exit(0 if result['exists'] else 1)
    else:
        sys.exit(2)
