#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速核查：在配置的详单表中查询通行标识ID（优化版）
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import load_config


def quick_check(pass_id: str):
    """快速查询"""
    from database import get_db_connection
    
    config = load_config()
    table_name = config.get('DETAIL_QUERY', 'table_name', fallback='')
    
    print(f"配置表: {table_name}")
    print(f"查询ID: {pass_id}")
    
    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            # 直接查询，不先count
            try:
                sql = f"""SELECT `通行标识ID`, `实际车辆车牌号码+颜色`,
                        `收费入口名称`, `收费出口名称`
                        FROM `{table_name}`
                        WHERE `通行标识ID` = %s LIMIT 5"""
                
                cursor.execute(sql, (pass_id,))
                rows = cursor.fetchall()
                
                if rows:
                    print(f"\n✅ 找到 {len(rows)} 条记录:")
                    for idx, row in enumerate(rows, 1):
                        print(f"\n  记录{idx}:")
                        print(f"    ID: {row[0]}")
                        print(f"    车牌: {row[1]}")
                        print(f"    入口: {row[2]}")
                        print(f"    出口: {row[3]}")
                    return True
                else:
                    print(f"\n❌ 未找到记录")
                    
                    # 获取样本看看格式
                    cursor.execute(f"SELECT `通行标识ID` FROM `{table_name}` LIMIT 3")
                    samples = [r[0] for r in cursor.fetchall()]
                    if samples:
                        print(f"\n样本ID (前3条):")
                        for s in samples:
                            if s:
                                print(f"  • {str(s)[:50]}... (长度:{len(str(s))})")
                    return False
                    
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                return None


if __name__ == "__main__":
    target = "020000430101930023523020251211173306"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    result = quick_check(target)
    sys.exit(0 if result else 1)
