"""
健康检查路由
包含应用健康状态检查接口
"""

import logging
import platform
import time
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# 应用启动时间
start_time = time.time()


@router.get("/api/health")
async def health_check():
    """应用健康检查接口"""
    try:
        # 检查数据库连接状态
        db_status = check_database_health()
        
        # 计算运行时间
        uptime_seconds = int(time.time() - start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}小时{minutes}分{seconds}秒"
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "status": "healthy" if all(db.values()) else "degraded",
                "timestamp": datetime.now().isoformat(),
                "uptime": uptime_str,
                "uptimeSeconds": uptime_seconds,
                "system": {
                    "platform": platform.platform(),
                    "pythonVersion": platform.python_version(),
                    "hostname": platform.node()
                },
                "database": db_status,
                "services": {
                    "status": "running"
                }
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "code": 500,
            "message": "health check failed",
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }


def check_database_health() -> dict:
    """检查各数据库连接的健康状态"""
    db_status = {}
    
    try:
        from core.config import get_config as get_app_config
        from database import create_db_connection
        
        config = get_app_config()
        
        for db_key in ['REMOTE_DB', 'LOCAL_DB', 'USER_DB', 'CHECK_DATA_DB']:
            try:
                conn = create_db_connection(db_key, config)
                
                if conn and conn.open:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        
                        if result:
                            db_status[db_key] = True
                        else:
                            db_status[db_key] = False
                    
                    conn.close()
                else:
                    db_status[db_key] = False
                    
            except Exception as e:
                logger.debug(f"{db_key} 数据库检查失败: {e}")
                db_status[db_key] = False
                
    except Exception as e:
        logger.error(f"数据库健康检查异常: {e}")
        
        # 如果无法加载配置，返回所有数据库为不可用状态
        for db_key in ['REMOTE_DB', 'LOCAL_DB', 'USER_DB', 'CHECK_DATA_DB']:
            db_status[db_key] = False
    
    return db_status
