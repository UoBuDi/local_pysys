"""
同步管理路由
包含同步月份列表、启动/停止/暂停/强制停止同步、同步状态查询等接口
"""

import logging

from fastapi import APIRouter, Depends
from typing import Optional, List

from core.dependencies import get_current_user
from core.models import StartSyncRequest
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/sync/months/")
async def get_sync_months(user: dict = Depends(get_current_user)):
    """获取可用的同步月份列表"""
    try:
        config = get_app_config()
        from database import create_db_connection
        
        conn = create_db_connection("LOCAL_DB", config)
        
        if not conn:
            return {"code": 500, "message": "无法连接到本地数据库"}
        
        try:
            with conn.cursor() as cursor:
                # 查询所有表名（格式为：YYYYMM）
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                # 过滤出符合 YYYYMM 格式的表名（月度数据表）
                months = []
                for table in tables:
                    table_name = table[0]
                    # 匹配 6 位数字的表名（如 202401）
                    if len(table_name) == 6 and table_name.isdigit():
                        months.append({
                            "value": table_name,
                            "label": f"{table_name[:4]}年{int(table_name[4:]):02d}月"
                        })
                
                # 按时间倒序排列
                months.sort(key=lambda x: x['value'], reverse=True)
                
                return {
                    "code": 200,
                    "message": "success",
                    "data": months
                }
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"获取同步月份失败: {e}")
        return {"code": 500, "message": "获取同步月份失败"}


@router.post("/api/start-sync/")
async def start_sync(request: StartSyncRequest, user: dict = Depends(get_current_user)):
    """启动数据同步任务"""
    try:
        from sync_manager import sync_manager
        
        if not request.months:
            return {"code": 400, "message": "请选择要同步的月份"}
        
        success = await sync_manager.start_sync(request.months, user.get('username'))
        
        if success:
            return {
                "code": 200,
                "message": f"已提交 {len(request.months)} 个月的同步任务",
                "data": {
                    "months": request.months,
                    "status": "started"
                }
            }
        else:
            return {"code": 400, "message": "同步任务已在运行中或无法启动"}
            
    except Exception as e:
        logger.error(f"启动同步任务失败: {e}")
        return {"code": 500, "message": "启动同步任务失败"}


@router.post("/api/stop-sync/")
async def stop_sync(user: dict = Depends(get_current_user)):
    """停止当前同步任务"""
    try:
        from sync_manager import sync_manager
        
        success = await sync_manager.stop_sync()
        
        if success:
            return {
                "code": 200,
                "message": "同步任务正在停止",
                "data": {"status": "stopping"}
            }
        else:
            return {"code": 400, "message": "没有正在运行的同步任务"}
            
    except Exception as e:
        logger.error(f"停止同步任务失败: {e}")
        return {"code": 500, "message": "停止同步任务失败"}


@router.post("/api/pause-sync/")
async def pause_sync(user: dict = Depends(get_current_user)):
    """暂停当前同步任务"""
    try:
        from sync_manager import sync_manager
        
        success = await sync_manager.pause_sync()
        
        if success:
            return {
                "code": 200,
                "message": "同步任务已暂停",
                "data": {"status": "paused"}
            }
        else:
            return {"code": 400, "message": "没有正在运行的同步任务"}
            
    except Exception as e:
        logger.error(f"暂停同步任务失败: {e}")
        return {"code": 500, "message": "暂停同步任务失败"}


@router.post("/api/force-stop-sync/")
async def force_stop_sync(user: dict = Depends(get_current_user)):
    """强制停止同步任务（立即终止）"""
    try:
        from sync_manager import sync_manager
        
        success = await sync_manager.force_stop_sync()
        
        if success:
            return {
                "code": 200,
                "message": "同步任务已被强制终止",
                "data": {"status": "force_stopped"}
            }
        else:
            return {"code": 400, "message": "没有正在运行的同步任务"}
            
    except Exception as e:
        logger.error(f"强制停止同步任务失败: {e}")
        return {"code": 500, "message": "强制停止同步任务失败"}


@router.get("/api/sync/status/")
async def get_sync_status(user: dict = Depends(get_current_user)):
    """获取当前同步状态"""
    try:
        from sync_manager import sync_manager
        
        status = await sync_manager.get_status()
        
        return {
            "code": 200,
            "message": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return {"code": 500, "message": "获取同步状态失败"}
