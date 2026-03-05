import pymysql
import hashlib
import configparser
import os

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

try:
    conn = pymysql.connect(**get_db_config('USER_DB'))
except:
    conn = pymysql.connect(**get_db_config('LOCAL_DB'))

try:
    with conn.cursor() as cursor:
        # 重置admin用户密码为456123（MD5加密）
        new_password = '456123'
        md5_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        
        print(f"重置admin用户密码为: {new_password}")
        print(f"MD5哈希: {md5_hash}")
        
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (md5_hash, 'admin'))
        conn.commit()
        
        print(f"影响行数: {cursor.rowcount}")
        print("密码重置成功！")
        
finally:
    conn.close()
