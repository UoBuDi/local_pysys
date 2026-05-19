import pymysql
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

db_pools: Dict[str, PooledDB] = {}


def test_db_connection(host: str, port: int, user: str, password: str, database: str, charset: str = 'utf8mb4') -> bool:
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception:
        return False


def _build_pool_config(section: str, config, max_connections: int = 10) -> dict:
    """构建连接池配置参数"""
    return {
        'host': config.get(section, 'host', fallback='localhost'),
        'port': config.getint(section, 'port', fallback=3306),
        'user': config.get(section, 'user', fallback='root'),
        'password': config.get(section, 'password', fallback='password'),
        'database': config.get(section, 'database', fallback='test'),
        'charset': config.get(section, 'charset', fallback='utf8mb4'),
        'connect_timeout': 5,
        'read_timeout': 30,
        'write_timeout': 30,
        'maxconnections': max_connections,
        'mincached': 2,
        'maxcached': 5,
        'blocking': True,
        'ping': 1
    }


def create_db_pool(config, sections=None, max_connections: int = 10) -> None:
    """批量初始化连接池，为配置中所有数据库节创建连接池
    
    Args:
        config: configparser 配置对象
        sections: 要初始化的数据库节列表，默认自动从配置中读取
        max_connections: 每个池最大连接数
    """
    if sections is None:
        sections = [s for s in config.sections() if s.endswith('_DB')]
    
    for section in sections:
        if section in db_pools:
            logger.info(f"连接池 {section} 已存在，跳过重复创建")
            continue
        try:
            pool_config = _build_pool_config(section, config, max_connections)
            pool = PooledDB(pymysql, **pool_config)
            db_pools[section] = pool
            logger.info(f"连接池 {section} 创建成功，最大连接数={max_connections}")
        except Exception as e:
            logger.error(f"创建 {section} 连接池失败: {e}")


def create_db_connection(section: str, config) -> Optional[pymysql.connections.Connection]:
    """兼容旧接口：优先从连接池获取，无池时创建直连（已废弃，建议使用 get_db_connection）"""
    if section in db_pools:
        try:
            return db_pools[section].connection()
        except Exception as e:
            logger.warning(f"从连接池 {section} 获取连接失败: {e}")
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
    except Exception as e:
        logger.error(f"创建 {section} 直连失败: {e}")
        return None


@contextmanager
def get_db_connection(db_key: str, config):
    """统一的数据库连接上下文管理器，自动从连接池获取/归还连接
    
    用法：
        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT ...")
    """
    conn = None
    try:
        if db_key in db_pools:
            conn = db_pools[db_key].connection()
        else:
            db_cfg = {
                'host': config.get(db_key, 'host', fallback='localhost'),
                'port': config.getint(db_key, 'port', fallback=3306),
                'user': config.get(db_key, 'user', fallback='root'),
                'password': config.get(db_key, 'password', fallback='password'),
                'database': config.get(db_key, 'database', fallback='test'),
                'charset': config.get(db_key, 'charset', fallback='utf8mb4'),
                'connect_timeout': 5,
                'read_timeout': 30,
                'write_timeout': 30,
            }
            conn = pymysql.connect(**db_cfg)
            logger.warning(f"{db_key} 无连接池，使用直连")
        yield conn
    finally:
        if conn:
            conn.close()


@contextmanager
def transaction(conn):
    """事务上下文管理器，自动 commit / rollback
    
    用法：
        with get_db_connection("USER_DB", config) as conn:
            with transaction(conn):
                with conn.cursor() as cursor:
                    cursor.execute("DELETE ...")
                    cursor.execute("INSERT ...")
    """
    try:
        conn.begin()
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def close_all_pools() -> None:
    """关闭所有连接池并释放资源"""
    for section, pool in list(db_pools.items()):
        try:
            pool.close()
            logger.info(f"连接池 {section} 已关闭")
        except Exception as e:
            logger.error(f"关闭连接池 {section} 失败: {e}")
    db_pools.clear()


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
        conn = pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=5)
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
        conn.close()
        return databases
    except Exception:
        return []
