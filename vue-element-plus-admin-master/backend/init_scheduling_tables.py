import pymysql
import configparser
import os

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if os.path.exists(config_path):
        config.read(config_path)
    return config

def get_db_connection(config, section='USER_DB'):
    try:
        return pymysql.connect(
            host=config.get(section, 'host', fallback='localhost'),
            port=config.getint(section, 'port', fallback=3306),
            user=config.get(section, 'user', fallback='root'),
            password=config.get(section, 'password', fallback=''),
            database=config.get(section, 'database', fallback='system_db'),
            charset=config.get(section, 'charset', fallback='utf8mb4')
        )
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return None

def init_scheduling_tables():
    config = load_config()
    conn = get_db_connection(config, 'USER_DB')
    
    if not conn:
        print("无法连接到数据库")
        return False
    
    try:
        with conn.cursor() as cursor:
            print("开始创建排班相关表...")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduling_groups (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '班组ID',
                    name VARCHAR(100) NOT NULL COMMENT '班组名称',
                    description VARCHAR(500) COMMENT '班组描述',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    UNIQUE KEY uk_name (name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班组表'
            """)
            print("班组表创建成功")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduling_shifts (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '班次ID',
                    name VARCHAR(50) NOT NULL COMMENT '班次名称',
                    start_time TIME NOT NULL COMMENT '开始时间',
                    end_time TIME NOT NULL COMMENT '结束时间',
                    description VARCHAR(200) COMMENT '班次描述',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班次表'
            """)
            print("班次表创建成功")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduling_staff (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '人员ID',
                    name VARCHAR(50) NOT NULL COMMENT '姓名',
                    employee_id VARCHAR(50) COMMENT '工号',
                    group_id INT COMMENT '所属班组ID',
                    phone VARCHAR(20) COMMENT '联系电话',
                    status TINYINT DEFAULT 1 COMMENT '状态：1-在职，0-离职',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_group_id (group_id),
                    UNIQUE KEY uk_employee_id (employee_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人员表'
            """)
            print("人员表创建成功")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduling_records (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '排班记录ID',
                    staff_id INT NOT NULL COMMENT '人员ID',
                    group_id INT NOT NULL COMMENT '班组ID',
                    shift_id INT NOT NULL COMMENT '班次ID',
                    schedule_date DATE NOT NULL COMMENT '排班日期',
                    remark VARCHAR(500) COMMENT '备注',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_staff_id (staff_id),
                    INDEX idx_group_id (group_id),
                    INDEX idx_shift_id (shift_id),
                    INDEX idx_schedule_date (schedule_date),
                    UNIQUE KEY uk_staff_date_shift (staff_id, schedule_date, shift_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='排班记录表'
            """)
            print("排班记录表创建成功")
            
            cursor.execute("SELECT COUNT(*) FROM scheduling_shifts")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO scheduling_shifts (name, start_time, end_time, description) VALUES
                    ('早班', '08:00:00', '16:00:00', '上午8点至下午4点'),
                    ('中班', '16:00:00', '00:00:00', '下午4点至午夜12点'),
                    ('晚班', '00:00:00', '08:00:00', '午夜12点至上午8点')
                """)
                print("默认班次数据插入成功")
            
            cursor.execute("SELECT COUNT(*) FROM scheduling_groups")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO scheduling_groups (name, description) VALUES
                    ('一班', '第一班组'),
                    ('二班', '第二班组'),
                    ('三班', '第三班组')
                """)
                print("默认班组数据插入成功")
            
            conn.commit()
            print("排班表初始化完成!")
            return True
            
    except Exception as e:
        print(f"初始化排班表失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    init_scheduling_tables()
