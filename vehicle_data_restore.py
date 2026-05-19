#!/usr/bin/env python3
import pymysql
import sys
import time

# 数据库连接配置
db_config = {
    'host': '172.32.48.238',
    'port': 3306,
    'user': 'root',
    'password': '9a1d4e4ae72d2eaa',
    'database': 'branchdb',
    'charset': 'utf8mb4'
}

def main():
    print("开始还原2024-05月份车辆数据...")
    start_time = time.time()
    
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取2024-05月份的所有唯一hourBatchNo
        print("获取2024-05月份的hourBatchNo列表...")
        cursor.execute("""
            SELECT DISTINCT hourBatchNo 
            FROM `gbupload_etctu_as_2024-05` 
            WHERE transTime BETWEEN '2024-05-01 00:00:00' AND '2024-05-31 23:59:59'
            ORDER BY hourBatchNo
        """)
        hour_batch_nos = [row['hourBatchNo'] for row in cursor.fetchall()]
        
        total_batches = len(hour_batch_nos)
        print(f"共发现 {total_batches} 个批次")
        
        # 实现分批处理逻辑
        total_matched = 0
        total_unmatched = 0
        processed_batches = 0
        
        # 存储所有结果
        all_results = {
            'matched': [],
            'unmatched': []
        }
        
        for i, hour_batch in enumerate(hour_batch_nos):
            processed_batches += 1
            print(f"\n处理批次 {i+1}/{total_batches}: {hour_batch}")
            
            # 查询已匹配的数据
            matched_query = """
                SELECT 
                    ev.hourBatchNo, 
                    ev.vehiclePlate, 
                    ev.transTime, 
                    v.picTime,
                    TIMESTAMPDIFF(SECOND, ev.transTime, v.picTime) AS time_diff,
                    ev.gantryId AS etc_gantry,
                    v.gantryId AS viu_gantry,
                    ev.fee,
                    v.vehicleSpeed
                FROM 
                    branchdb.`gbupload_etctu_as_2024-05` ev
                INNER JOIN 
                    branchdb.`gbupload_viu` v 
                ON 
                    ev.hourBatchNo = v.hourBatchNo 
                    AND ev.vehiclePlate = v.vehiclePlate
                    AND ABS(TIMESTAMPDIFF(SECOND, ev.transTime, v.picTime)) <= 30
                WHERE 
                    ev.hourBatchNo = %s
                    AND ev.transTime BETWEEN '2024-05-01 00:00:00' AND '2024-05-31 23:59:59'
                    AND v.picTime BETWEEN '2024-05-01 00:00:00' AND '2024-05-31 23:59:59'
                ORDER BY ev.transTime
            """
            
            cursor.execute(matched_query, (hour_batch,))
            matched_results = cursor.fetchall()
            batch_matched = len(matched_results)
            total_matched += batch_matched
            all_results['matched'].extend(matched_results)
            
            # 查询未匹配的数据
            unmatched_query = """
                SELECT 
                    ev.hourBatchNo, 
                    ev.vehiclePlate, 
                    ev.transTime, 
                    ev.gantryId AS etc_gantry,
                    ev.fee
                FROM 
                    branchdb.`gbupload_etctu_as_2024-05` ev
                LEFT JOIN 
                    branchdb.`gbupload_viu` v 
                ON 
                    ev.hourBatchNo = v.hourBatchNo 
                    AND ev.vehiclePlate = v.vehiclePlate
                    AND ABS(TIMESTAMPDIFF(SECOND, ev.transTime, v.picTime)) <= 30
                WHERE 
                    ev.hourBatchNo = %s
                    AND ev.transTime BETWEEN '2024-05-01 00:00:00' AND '2024-05-31 23:59:59'
                    AND v.hourBatchNo IS NULL
                ORDER BY ev.transTime
            """
            
            cursor.execute(unmatched_query, (hour_batch,))
            unmatched_results = cursor.fetchall()
            batch_unmatched = len(unmatched_results)
            total_unmatched += batch_unmatched
            all_results['unmatched'].extend(unmatched_results)
            
            # 显示当前批次的统计
            print(f"  已匹配: {batch_matched} 条, 未匹配: {batch_unmatched} 条")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        # 输出统计信息
        print(f"\n=== 总统计信息 ===")
        print(f"总处理批次: {processed_batches}/{total_batches}")
        print(f"已匹配记录总数: {total_matched}")
        print(f"未匹配记录总数: {total_unmatched}")
        print(f"总记录数: {total_matched + total_unmatched}")
        
        # 提供结果查看选项
        print("\n=== 结果查看选项 ===")
        print("1. 查看已匹配结果")
        print("2. 查看未匹配结果")
        print("3. 退出")
        
        while True:
            choice = input("\n请选择要查看的结果类型 (1-3): ")
            if choice == '1':
                print(f"\n=== 已匹配结果 ({total_matched} 条) ===")
                if all_results['matched']:
                    print("前10条记录示例：")
                    for i, record in enumerate(all_results['matched'][:10]):
                        print(f"  {i+1}. 车牌号: {record['vehiclePlate']}, ETC时间: {record['transTime']}, 图片时间: {record['picTime']}, 时间差: {record['time_diff']}秒, ETC门架: {record['etc_gantry']}, VIU门架: {record['viu_gantry']}")
                else:
                    print("没有已匹配的记录")
            elif choice == '2':
                print(f"\n=== 未匹配结果 ({total_unmatched} 条) ===")
                if all_results['unmatched']:
                    print("前10条记录示例：")
                    for i, record in enumerate(all_results['unmatched'][:10]):
                        print(f"  {i+1}. 车牌号: {record['vehiclePlate']}, ETC时间: {record['transTime']}, ETC门架: {record['etc_gantry']}")
                else:
                    print("没有未匹配的记录")
            elif choice == '3':
                print("\n退出查看")
                break
            else:
                print("无效的选择，请重新输入")
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)
    
    end_time = time.time()
    print(f"\n完成！总耗时: {end_time - start_time:.2f}秒")

if __name__ == "__main__":
    main()
1