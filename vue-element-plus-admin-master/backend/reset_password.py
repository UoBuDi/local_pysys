import pymysql
import hashlib
import configparser
import os
import sys
import argparse

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

def get_db_connection():
    try:
        return pymysql.connect(**get_db_config('USER_DB'))
    except:
        try:
            return pymysql.connect(**get_db_config('LOCAL_DB'))
        except Exception as e:
            print(f"数据库连接失败: {e}")
            sys.exit(1)

def list_users(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username, nickname, status FROM users ORDER BY id")
        users = cursor.fetchall()
        print("\n当前系统用户列表:")
        print("-" * 50)
        for user in users:
            status_text = "启用" if user['status'] == 1 else "禁用"
            print(f"ID: {user['id']}, 用户名: {user['username']}, 昵称: {user['nickname'] or 'N/A'}, 状态: {status_text}")
        print("-" * 50)
        return users

def reset_password_by_username(conn, username, new_password):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return False
        
        md5_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (md5_hash, username))
        conn.commit()
        
        print(f"\n密码重置成功!")
        print(f"用户名: {username}")
        print(f"新密码: {new_password}")
        print(f"MD5哈希: {md5_hash}")
        print(f"影响行数: {cursor.rowcount}")
        return True

def reset_password_by_id(conn, user_id, new_password):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"错误: 用户ID '{user_id}' 不存在")
            return False
        
        md5_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (md5_hash, user_id))
        conn.commit()
        
        print(f"\n密码重置成功!")
        print(f"用户ID: {user_id}")
        print(f"用户名: {user['username']}")
        print(f"新密码: {new_password}")
        print(f"MD5哈希: {md5_hash}")
        print(f"影响行数: {cursor.rowcount}")
        return True

def interactive_mode(conn):
    list_users(conn)
    
    while True:
        print("\n请选择操作方式:")
        print("1. 通过用户名重置密码")
        print("2. 通过用户ID重置密码")
        print("3. 退出")
        
        choice = input("\n请输入选项 (1/2/3): ").strip()
        
        if choice == '3':
            print("已退出")
            break
        
        if choice not in ['1', '2']:
            print("无效选项，请重新选择")
            continue
        
        if choice == '1':
            username = input("请输入用户名: ").strip()
            if not username:
                print("用户名不能为空")
                continue
        else:
            try:
                user_id = int(input("请输入用户ID: ").strip())
            except ValueError:
                print("用户ID必须是数字")
                continue
        
        new_password = input("请输入新密码 (直接回车使用默认密码 '123456'): ").strip()
        if not new_password:
            new_password = '123456'
        
        confirm = input(f"确认重置密码? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消操作")
            continue
        
        if choice == '1':
            reset_password_by_username(conn, username, new_password)
        else:
            reset_password_by_id(conn, user_id, new_password)

def main():
    parser = argparse.ArgumentParser(description='用户密码重置工具')
    parser.add_argument('-u', '--username', help='要重置密码的用户名')
    parser.add_argument('-i', '--user-id', type=int, help='要重置密码的用户ID')
    parser.add_argument('-p', '--password', help='新密码 (默认: 123456)')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有用户')
    parser.add_argument('--interactive', action='store_true', help='交互式模式')
    
    args = parser.parse_args()
    
    conn = get_db_connection()
    
    try:
        if args.list:
            list_users(conn)
        elif args.interactive or len(sys.argv) == 1:
            interactive_mode(conn)
        elif args.username:
            new_password = args.password or '123456'
            reset_password_by_username(conn, args.username, new_password)
        elif args.user_id:
            new_password = args.password or '123456'
            reset_password_by_id(conn, args.user_id, new_password)
        else:
            parser.print_help()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
