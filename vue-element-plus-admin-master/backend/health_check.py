import psutil
import os
from datetime import datetime
from typing import Dict, Any
from database import create_db_connection
import configparser

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
config = configparser.ConfigParser()
config.read(config_file, encoding='utf-8')

async def check_database_health() -> Dict[str, Any]:
    try:
        conn = create_db_connection("USER_DB", config)
        if conn:
            conn.close()
            return {"status": "healthy", "message": "数据库连接正常"}
        return {"status": "unhealthy", "message": "数据库连接失败"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

async def check_websocket_health(active_connections: int) -> Dict[str, Any]:
    return {
        "status": "healthy",
        "message": "WebSocket服务正常",
        "active_connections": active_connections
    }

async def check_memory_usage() -> Dict[str, Any]:
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        status = "healthy" if memory_percent < 80 else "warning" if memory_percent < 90 else "unhealthy"
        
        return {
            "status": status,
            "message": f"内存使用率: {memory_percent:.1f}%",
            "usage_percent": round(memory_percent, 2),
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2)
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"内存检查失败: {str(e)}"}

async def check_disk_usage() -> Dict[str, Any]:
    try:
        disk = psutil.disk_usage('/')
        usage_percent = disk.percent
        
        status = "healthy" if usage_percent < 80 else "warning" if usage_percent < 90 else "unhealthy"
        
        return {
            "status": status,
            "message": f"磁盘使用率: {usage_percent:.1f}%",
            "usage_percent": round(usage_percent, 2),
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"磁盘检查失败: {str(e)}"}

async def get_health_status(active_connections: int = 0) -> Dict[str, Any]:
    checks = {
        "database": await check_database_health(),
        "websocket": await check_websocket_health(active_connections),
        "memory": await check_memory_usage(),
        "disk": await check_disk_usage()
    }
    
    overall_status = "healthy"
    for check in checks.values():
        if check["status"] == "unhealthy":
            overall_status = "degraded"
            break
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "checks": checks
    }
