import pymysql
import configparser
import os
from datetime import datetime

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
config = configparser.ConfigParser()
config.read(config_file, encoding='utf-8')

def get_db_config(db_section):
    return {
        'host': config.get(db_section, 'host'),
        'port': config.getint(db_section, 'port'),
        'user': config.get(db_section, 'user'),
        'password': config.get(db_section, 'password'),
        'database': config.get(db_section, 'database'),
        'charset': config.get(db_section, 'charset', fallback='utf8mb4'),
        'cursorclass': pymysql.cursors.DictCursor
    }

def create_tables():
    try:
        conn = pymysql.connect(**get_db_config('USER_DB'))
    except:
        conn = pymysql.connect(**get_db_config('LOCAL_DB'))
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_statistics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stat_date DATE NOT NULL COMMENT '统计日期',
                    stat_month VARCHAR(7) NOT NULL COMMENT '统计月份',
                    total_transactions BIGINT DEFAULT 0 COMMENT '总交易数',
                    total_amount DECIMAL(18, 2) DEFAULT 0 COMMENT '总交易金额',
                    total_split_amount DECIMAL(18, 2) DEFAULT 0 COMMENT '总拆分金额',
                    station_count INT DEFAULT 0 COMMENT '收费站数量',
                    vehicle_types JSON COMMENT '车型分布统计',
                    daily_transactions JSON COMMENT '每日交易数统计',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_stat_date (stat_date),
                    INDEX idx_stat_month (stat_month)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Dashboard统计数据表'
            """)
            print("创建 dashboard_statistics 表成功")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task_name VARCHAR(100) NOT NULL COMMENT '任务名称',
                    task_type VARCHAR(50) NOT NULL COMMENT '任务类型',
                    cron_expression VARCHAR(100) COMMENT 'Cron表达式',
                    is_enabled TINYINT DEFAULT 1 COMMENT '是否启用',
                    last_run_time DATETIME COMMENT '上次执行时间',
                    next_run_time DATETIME COMMENT '下次执行时间',
                    last_run_status VARCHAR(20) COMMENT '上次执行状态',
                    last_run_message TEXT COMMENT '上次执行消息',
                    config JSON COMMENT '任务配置',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_task_name (task_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务配置表'
            """)
            print("创建 scheduled_tasks 表成功")
            
            cursor.execute("""
                INSERT IGNORE INTO scheduled_tasks (task_name, task_type, cron_expression, is_enabled, config)
                VALUES ('dashboard_statistics_daily', 'statistics', '0 2 * * *', 1, '{"description": "每日凌晨2点统计Dashboard数据"}')
            """)
            print("插入默认定时任务配置成功")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_execution_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task_name VARCHAR(100) NOT NULL COMMENT '任务名称',
                    start_time DATETIME NOT NULL COMMENT '开始时间',
                    end_time DATETIME COMMENT '结束时间',
                    status VARCHAR(20) NOT NULL COMMENT '执行状态',
                    message TEXT COMMENT '执行消息',
                    details JSON COMMENT '执行详情',
                    duration_seconds INT COMMENT '执行耗时(秒)',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_task_name (task_name),
                    INDEX idx_start_time (start_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务执行历史表'
            """)
            print("创建 task_execution_history 表成功")
            
            conn.commit()
            print("\n所有表创建完成!")
            
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
