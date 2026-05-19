import pymysql
import configparser
import sys

def execute_migration():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    db_config = {
        'host': config.get('USER_DB', 'host', fallback='localhost'),
        'port': config.getint('USER_DB', 'port', fallback=3306),
        'user': config.get('USER_DB', 'user', fallback='root'),
        'password': config.get('USER_DB', 'password', fallback='password'),
        'database': config.get('USER_DB', 'database', fallback='test'),
        'charset': 'utf8mb4'
    }

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    try:
        with open('migrations/002_permission_granularity.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            cursor.execute(sql)
            conn.commit()
            print('权限粒度优化迁移成功')
    except Exception as e:
        print(f'迁移失败: {e}')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    execute_migration()
