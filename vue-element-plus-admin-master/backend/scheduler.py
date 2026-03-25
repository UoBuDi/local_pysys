import threading
import time
import schedule
import logging
from datetime import datetime
from statistics_service import run_statistics_task, update_task_status
import pymysql
import configparser
import os

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
config = configparser.ConfigParser()
config.read(config_file, encoding='utf-8')

logger = logging.getLogger(__name__)

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

def get_user_db_connection():
    try:
        return pymysql.connect(**get_db_config('USER_DB'))
    except:
        return pymysql.connect(**get_db_config('LOCAL_DB'))

def get_task_config(task_name: str) -> dict:
    conn = get_user_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM scheduled_tasks WHERE task_name = %s",
                (task_name,)
            )
            task = cursor.fetchone()
            return task if task else {}
    finally:
        conn.close()

def run_dashboard_statistics():
    task_name = 'dashboard_statistics_daily'
    
    task_config = get_task_config(task_name)
    
    if not task_config or task_config.get('is_enabled') != 1:
        logger.info(f"任务 {task_name} 未启用，跳过执行")
        return
    
    logger.info(f"开始执行定时任务: {task_name}")
    
    result = run_statistics_task()
    
    status = 'success' if result['success'] else 'failed'
    update_task_status(task_name, status, result['message'])
    
    logger.info(f"任务 {task_name} 执行完成: {result['message']}")

def parse_cron_expression(cron_expr: str) -> dict:
    parts = cron_expr.split()
    if len(parts) != 5:
        return None
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day': parts[2],
        'month': parts[3],
        'day_of_week': parts[4]
    }

def setup_scheduled_tasks():
    conn = get_user_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT task_name, cron_expression, is_enabled FROM scheduled_tasks WHERE is_enabled = 1"
            )
            tasks = cursor.fetchall()
            
            for task in tasks:
                task_name = task['task_name']
                cron_expr = task['cron_expression']
                
                if not cron_expr:
                    continue
                
                cron_parts = parse_cron_expression(cron_expr)
                if not cron_parts:
                    continue
                
                if task_name == 'dashboard_statistics_daily':
                    minute = cron_parts['minute']
                    hour = cron_parts['hour']
                    
                    if minute == '*' or hour == '*':
                        schedule.every().day.at("02:00").do(run_dashboard_statistics)
                    else:
                        time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"
                        schedule.every().day.at(time_str).do(run_dashboard_statistics)
                    
                    logger.info(f"已注册定时任务: {task_name}, 执行时间: {cron_expr}")
    finally:
        conn.close()

_scheduler_thread = None
_stop_event = threading.Event()

def scheduler_loop():
    while not _stop_event.is_set():
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    global _scheduler_thread, _stop_event
    
    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.warning("定时任务调度器已在运行")
        return
    
    _stop_event.clear()
    
    setup_scheduled_tasks()
    
    _scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    _scheduler_thread.start()
    
    logger.info("定时任务调度器已启动")

def stop_scheduler():
    global _stop_event
    
    _stop_event.set()
    schedule.clear()
    logger.info("定时任务调度器已停止")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    start_scheduler()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
        print("调度器已停止")
