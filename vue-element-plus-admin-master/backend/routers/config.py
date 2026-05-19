"""
配置管理路由
包含系统配置的获取、保存、测试连接以及数据库表列表查询等接口
"""

import logging

import pymysql
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import configparser

from core.dependencies import get_current_user
from core.models import FullConfigRequest, DatabaseConfig, TestConnectionRequest
from core.config import get_config as get_app_config, save_config_to_file, update_global_config
from core.security import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)

router = APIRouter()

PASSWORD_MASK = '***'


def _mask_password(password: str) -> str:
    """将密码统一遮罩为固定占位符，避免部分遮罩被回写覆盖真实密码"""
    if password:
        return PASSWORD_MASK
    return ''


def _resolve_test_password(request: TestConnectionRequest, section: str) -> str:
    """解析测试连接使用的密码：优先使用前端传入的新密码，其次使用已存储的密码"""
    if request.password and request.password != PASSWORD_MASK:
        return request.password

    if request.use_stored_password:
        config = get_app_config()
        stored = config.get(section, 'password', fallback='')
        if stored:
            return decrypt_password(stored)

    return request.password or ''


def _write_db_section(config: configparser.ConfigParser, section: str, db_config: DatabaseConfig):
    """将单个数据库配置节写入 config 对象"""
    if not config.has_section(section):
        config.add_section(section)

    config.set(section, 'host', db_config.host)
    config.set(section, 'port', str(db_config.port))
    config.set(section, 'user', db_config.user)
    config.set(section, 'database', db_config.database)
    config.set(section, 'charset', db_config.charset)

    if db_config.password and db_config.password != PASSWORD_MASK:
        encrypted = encrypt_password(db_config.password)
        config.set(section, 'password', encrypted)


@router.get("/api/config/")
async def get_config(user: dict = Depends(get_current_user)):
    """获取系统配置信息（含远程/本地数据库 + 同步参数）"""
    try:
        config = get_app_config()

        config_dict = {}
        for section in ['REMOTE_DB', 'LOCAL_DB', 'USER_DB', 'SYNC']:
            if not config.has_section(section):
                continue
            config_dict[section] = dict(config.items(section))

            if 'password' in config_dict[section]:
                config_dict[section]['password'] = _mask_password(
                    config_dict[section]['password']
                )

        return {
            "code": 200,
            "message": "success",
            "data": config_dict
        }
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        return {"code": 500, "message": "获取系统配置失败"}


@router.post("/api/config/")
async def save_config(request: FullConfigRequest, user: dict = Depends(get_current_user)):
    """保存完整系统配置（远程/本地数据库 + 同步参数）"""
    try:
        config = get_app_config()

        _write_db_section(config, 'REMOTE_DB', request.REMOTE_DB)
        _write_db_section(config, 'LOCAL_DB', request.LOCAL_DB)

        if not config.has_section('SYNC'):
            config.add_section('SYNC')
        config.set('SYNC', 'batch_size', request.SYNC.batch_size)
        config.set('SYNC', 'retry_count', request.SYNC.retry_count)
        config.set('SYNC', 'timeout', request.SYNC.timeout)
        config.set('SYNC', 'primary_keys', request.SYNC.primary_keys)
        if request.SYNC.default_month is not None:
            config.set('SYNC', 'default_month', request.SYNC.default_month)

        success = save_config_to_file(config)

        if success:
            update_global_config(config)

            try:
                from database import close_all_pools, create_db_pool
                close_all_pools()
                create_db_pool(config)
                logger.info("配置保存后已重建数据库连接池")
            except Exception as pool_err:
                logger.warning(f"重建数据库连接池失败: {pool_err}")

            return {
                "code": 200,
                "message": "配置保存成功",
                "data": {"status": "saved"}
            }
        else:
            return {"code": 500, "message": "配置保存失败"}

    except Exception as e:
        logger.error(f"保存系统配置失败: {e}")
        return {"code": 500, "message": "保存系统配置失败"}


@router.post("/api/config/test-remote/")
async def test_remote_connection(request: TestConnectionRequest, user: dict = Depends(get_current_user)):
    """测试远程数据库连接"""
    try:
        password = _resolve_test_password(request, 'REMOTE_DB')

        conn = pymysql.connect(
            host=request.host,
            port=request.port,
            user=request.user,
            password=password,
            database=request.database,
            charset=request.charset,
            connect_timeout=5
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result:
                    return {
                        "code": 200,
                        "message": "远程数据库连接成功",
                        "data": {
                            "status": "connected",
                            "host": request.host,
                            "port": request.port,
                            "database": request.database
                        }
                    }
                else:
                    return {
                        "code": 500,
                        "message": "远程数据库连接测试失败"
                    }
        finally:
            conn.close()

    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:
            return {"code": 401, "message": "用户名或密码错误"}
        elif error_code == 2003:
            return {"code": 503, "message": f"无法连接到服务器 {request.host}:{request.port}"}
        elif error_code == 1049:
            return {"code": 404, "message": f"数据库 '{request.database}' 不存在"}
        else:
            return {"code": 500, "message": f"连接错误 (错误码: {error_code}): {e.args[1]}"}
    except Exception as e:
        logger.error(f"测试远程数据库连接失败: {e}")
        return {"code": 500, "message": f"连接失败: {str(e)}"}


@router.post("/api/config/test-local/")
async def test_local_connection(request: TestConnectionRequest, user: dict = Depends(get_current_user)):
    """测试本地数据库连接"""
    try:
        password = _resolve_test_password(request, 'LOCAL_DB')

        conn = pymysql.connect(
            host=request.host,
            port=request.port,
            user=request.user,
            password=password,
            database=request.database,
            charset=request.charset,
            connect_timeout=5
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result:
                    return {
                        "code": 200,
                        "message": "本地数据库连接成功",
                        "data": {
                            "status": "connected",
                            "host": request.host,
                            "port": request.port,
                            "database": request.database
                        }
                    }
                else:
                    return {
                        "code": 500,
                        "message": "本地数据库连接测试失败"
                    }
        finally:
            conn.close()

    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:
            return {"code": 401, "message": "用户名或密码错误"}
        elif error_code == 2003:
            return {"code": 503, "message": f"无法连接到服务器 {request.host}:{request.port}"}
        elif error_code == 1049:
            return {"code": 404, "message": f"数据库 '{request.database}' 不存在"}
        else:
            return {"code": 500, "message": f"连接错误 (错误码: {error_code}): {e.args[1]}"}
    except Exception as e:
        logger.error(f"测试本地数据库连接失败: {e}")
        return {"code": 500, "message": f"连接失败: {str(e)}"}


@router.get("/api/database/tables/remote/")
async def get_remote_database_tables(user: dict = Depends(get_current_user)):
    """获取远程数据库的所有表列表"""
    try:
        config = get_app_config()
        from database import create_db_connection

        conn = create_db_connection("REMOTE_DB", config)

        if not conn:
            return {"code": 500, "message": "无法连接到远程数据库"}

        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()

                table_list = [table[0] for table in tables]

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "tables": table_list,
                        "count": len(table_list)
                    }
                }
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"获取远程数据库表列表失败: {e}")
        return {"code": 500, "message": "获取远程数据库表列表失败"}


@router.get("/api/database/tables/local/")
async def get_local_database_tables(user: dict = Depends(get_current_user)):
    """获取本地数据库的所有表列表"""
    try:
        config = get_app_config()
        from database import create_db_connection

        conn = create_db_connection("LOCAL_DB", config)

        if not conn:
            return {"code": 500, "message": "无法连接到本地数据库"}

        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()

                table_list = [table[0] for table in tables]

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "tables": table_list,
                        "count": len(table_list)
                    }
                }
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"获取本地数据库表列表失败: {e}")
        return {"code": 500, "message": "获取本地数据库表列表失败"}
