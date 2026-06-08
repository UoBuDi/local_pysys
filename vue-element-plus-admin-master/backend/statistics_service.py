import pymysql
import configparser
import os
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

VEHICLE_TYPE_MAP = {
    '1': '客一', '2': '客二', '3': '客三', '4': '客四',
    '11': '货一', '12': '货二', '13': '货三', '14': '货四', '15': '货五', '16': '货六',
    '21': '专一', '22': '专二', '23': '专三', '24': '专四', '25': '专五', '26': '专六'
}

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
config = configparser.ConfigParser()
config.read(config_file, encoding='utf-8')

def get_db_config(db_section: str) -> dict:
    return {
        'host': config.get(db_section, 'host'),
        'port': config.getint(db_section, 'port'),
        'user': config.get(db_section, 'user'),
        'password': config.get(db_section, 'password'),
        'database': config.get(db_section, 'database'),
        'charset': config.get(db_section, 'charset', fallback='utf8mb4'),
        'cursorclass': pymysql.cursors.DictCursor
    }

def get_check_data_connection():
    return pymysql.connect(**get_db_config('CHECK_DATA_DB'))

def get_user_db_connection():
    try:
        return pymysql.connect(**get_db_config('USER_DB'))
    except:
        return pymysql.connect(**get_db_config('LOCAL_DB'))

def get_table_name() -> str:
    return config.get('PATH_MATCH', 'table_name', fallback='202005-202311_cf_1215')

def get_vehicle_type_name(code: str) -> str:
    return VEHICLE_TYPE_MAP.get(str(code), f'未知({code})')

def get_latest_month_data() -> Dict[str, Any]:
    table_name = get_table_name()
    conn = get_check_data_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT 拆分月份, COUNT(*) as total_count 
                FROM `{table_name}` 
                GROUP BY 拆分月份 
                ORDER BY 拆分月份 DESC 
                LIMIT 1
            """)
            latest = cursor.fetchone()
            
            if not latest:
                return None
            
            latest_month = latest['拆分月份']
            
            cursor.execute(f"""
                SELECT 
                    COUNT(`通行标识ID`) as total_tx_count,
                    COALESCE(SUM(CAST(`拆分路段拆分金额` AS DECIMAL(18,2))), 0) as split_section_amount
                FROM `{table_name}`
                WHERE `拆分月份` = %s
                  AND `拆分类型/数据类型` != 36
            """, (latest_month,))
            amount_data = cursor.fetchone()
            
            cursor.execute(f"""
                SELECT 
                    COUNT(`通行标识ID`) as free_tx_count
                FROM `{table_name}`
                WHERE `拆分月份` = %s
                  AND `拆分类型/数据类型` = 36
            """, (latest_month,))
            free_data = cursor.fetchone()
            
            total_transactions = amount_data['total_tx_count']
            free_transactions = free_data['free_tx_count']
            
            cursor.execute(f"""
                SELECT 收费车型, COUNT(*) as count 
                FROM `{table_name}` 
                WHERE 拆分月份 = %s
                GROUP BY 收费车型
                ORDER BY count DESC
                LIMIT 10
            """, (latest_month,))
            vehicle_types = cursor.fetchall()
            
            cursor.execute(f"""
                SELECT 通行介质, COUNT(*) as count 
                FROM `{table_name}` 
                WHERE 拆分月份 = %s
                  AND `拆分类型/数据类型` != 36
                GROUP BY 通行介质
                ORDER BY count DESC
            """, (latest_month,))
            media_types = cursor.fetchall()
            
            cursor.execute(f"""
                SELECT t2.`省份名称`, COUNT(t1.`通行标识ID`) AS tx_count
                FROM `{table_name}` AS t1
                LEFT JOIN yin_wu.station_prov AS t2 ON LEFT(t1.`收费入口编码`, 14) = t2.`收费站编码`
                WHERE t1.`拆分月份` = %s
                GROUP BY t2.`省份名称`
                ORDER BY tx_count DESC
                LIMIT 20
            """, (latest_month,))
            province_data = cursor.fetchall()
            
            return {
                'stat_date': datetime.now().date(),
                'stat_month': latest_month,
                'total_transactions': total_transactions,
                'free_transactions': free_transactions,
                'split_section_amount': float(amount_data['split_section_amount'] or 0) / 100,
                'vehicle_types': json.dumps([
                    {'type': get_vehicle_type_name(item['收费车型']), 'code': item['收费车型'], 'count': item['count']} 
                    for item in vehicle_types
                ], ensure_ascii=False),
                'media_types': json.dumps([
                    {'type': item['通行介质'], 'count': item['count']} 
                    for item in media_types
                ], ensure_ascii=False),
                'province_data': json.dumps([
                    {'province': item['省份名称'] or '未知', 'count': item['tx_count']} 
                    for item in province_data
                ], ensure_ascii=False)
            }
    finally:
        conn.close()

def save_statistics(data: Dict[str, Any]) -> bool:
    conn = get_user_db_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO dashboard_statistics 
                (stat_date, stat_month, total_transactions, free_transactions, split_section_amount, 
                 vehicle_types, media_types, province_data)
                VALUES (%(stat_date)s, %(stat_month)s, %(total_transactions)s, %(free_transactions)s, 
                        %(split_section_amount)s, %(vehicle_types)s, %(media_types)s, %(province_data)s)
                ON DUPLICATE KEY UPDATE
                    stat_month = VALUES(stat_month),
                    total_transactions = VALUES(total_transactions),
                    free_transactions = VALUES(free_transactions),
                    split_section_amount = VALUES(split_section_amount),
                    vehicle_types = VALUES(vehicle_types),
                    media_types = VALUES(media_types),
                    province_data = VALUES(province_data),
                    updated_at = CURRENT_TIMESTAMP
            """, data)
            conn.commit()
            return True
    except Exception as e:
        print(f"保存统计数据失败: {e}")
        return False
    finally:
        conn.close()

def get_dashboard_statistics(stat_month: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_user_db_connection()
    
    try:
        with conn.cursor() as cursor:
            normalized_month = None
            if stat_month:
                normalized_month = stat_month.replace('-', '')
                if len(normalized_month) == 6 and normalized_month.isdigit():
                    normalized_month = f"{normalized_month[:4]}-{normalized_month[4:]}"
                else:
                    normalized_month = stat_month

            if normalized_month:
                cursor.execute("""
                    SELECT * FROM dashboard_statistics
                    WHERE stat_month = %s
                    ORDER BY stat_date DESC
                    LIMIT 1
                """, (normalized_month,))
            else:
                cursor.execute("""
                    SELECT * FROM dashboard_statistics 
                    ORDER BY stat_date DESC 
                    LIMIT 1
                """)
            data = cursor.fetchone()
            
            if data:
                data['vehicle_types'] = json.loads(data['vehicle_types']) if data['vehicle_types'] else []
                data['media_types'] = json.loads(data['media_types']) if data['media_types'] else []
                data['province_data'] = json.loads(data['province_data']) if data['province_data'] else []
            
            return data
    finally:
        conn.close()

def run_statistics_task() -> Dict[str, Any]:
    result = {
        'success': False,
        'message': '',
        'data': None,
        'executed_at': datetime.now().isoformat()
    }
    
    try:
        data = get_latest_month_data()
        
        if not data:
            result['message'] = '没有找到最新月份数据'
            return result
        
        if save_statistics(data):
            result['success'] = True
            result['message'] = f"成功统计 {data['stat_month']} 月份数据"
            result['data'] = data
        else:
            result['message'] = '保存统计数据失败'
            
    except Exception as e:
        result['message'] = f'统计任务执行失败: {str(e)}'
    
    return result

def update_task_status(task_name: str, status: str, message: str):
    conn = get_user_db_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE scheduled_tasks 
                SET last_run_time = NOW(),
                    last_run_status = %s,
                    last_run_message = %s,
                    updated_at = NOW()
                WHERE task_name = %s
            """, (status, message, task_name))
            conn.commit()
    finally:
        conn.close()

def start_task_execution(task_name: str) -> int:
    conn = get_user_db_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_execution_history 
                (task_name, start_time, status, message)
                VALUES (%s, NOW(), 'running', '任务开始执行')
            """, (task_name,))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def end_task_execution(history_id: int, status: str, message: str, details: dict = None, duration: int = None):
    conn = get_user_db_connection()
    
    try:
        with conn.cursor() as cursor:
            details_json = json.dumps(details, ensure_ascii=False, cls=DateTimeEncoder) if details else None
            cursor.execute("""
                UPDATE task_execution_history 
                SET end_time = NOW(),
                    status = %s,
                    message = %s,
                    details = %s,
                    duration_seconds = %s
                WHERE id = %s
            """, (status, message, details_json, duration, history_id))
            conn.commit()
    finally:
        conn.close()

def get_task_execution_history(task_name: str = None, limit: int = 20) -> list:
    conn = get_user_db_connection()
    
    try:
        with conn.cursor() as cursor:
            if task_name:
                cursor.execute("""
                    SELECT id, task_name, start_time, end_time, status, message, 
                           details, duration_seconds, created_at
                    FROM task_execution_history
                    WHERE task_name = %s
                    ORDER BY start_time DESC
                    LIMIT %s
                """, (task_name, limit))
            else:
                cursor.execute("""
                    SELECT id, task_name, start_time, end_time, status, message, 
                           details, duration_seconds, created_at
                    FROM task_execution_history
                    ORDER BY start_time DESC
                    LIMIT %s
                """, (limit,))
            
            results = cursor.fetchall()
            
            for row in results:
                if row['start_time']:
                    row['start_time'] = row['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                if row['end_time']:
                    row['end_time'] = row['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                if row['created_at']:
                    row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if row['details']:
                    row['details'] = json.loads(row['details'])
            
            return results
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始执行Dashboard统计任务...")
    result = run_statistics_task()
    print(f"执行结果: {result['message']}")
    if result['success']:
        print(f"统计数据: {json.dumps(result['data'], indent=2, ensure_ascii=False, default=str)}")
