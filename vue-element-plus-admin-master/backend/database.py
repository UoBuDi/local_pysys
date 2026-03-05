import pymysql
from typing import Optional, List, Dict

def test_db_connection(host: str, port: int, user: str, password: str, database: str, charset: str = 'utf8mb4') -> bool:
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset
        )
        conn.close()
        return True
    except Exception:
        return False

def create_db_connection(section: str, config) -> Optional[pymysql.connections.Connection]:
    try:
        db_config = {
            'host': config.get(section, 'host', fallback='localhost'),
            'port': config.getint(section, 'port', fallback=3306),
            'user': config.get(section, 'user', fallback='root'),
            'password': config.get(section, 'password', fallback='password'),
            'database': config.get(section, 'database', fallback='test'),
            'charset': config.get(section, 'charset', fallback='utf8mb4')
        }
        conn = pymysql.connect(**db_config)
        return conn
    except Exception:
        return None

def get_database_tables(conn: pymysql.connections.Connection) -> List[str]:
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
        return tables
    except Exception:
        return []

def table_exists(conn: pymysql.connections.Connection, table_name: str) -> bool:
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            return cursor.fetchone() is not None
    except Exception:
        return False

def get_available_databases(host: str, port: int, user: str, password: str) -> List[str]:
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password)
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
        conn.close()
        return databases
    except Exception:
        return []

def create_db_pool(config) -> Dict:
    return {}

def close_all_pools() -> None:
    pass