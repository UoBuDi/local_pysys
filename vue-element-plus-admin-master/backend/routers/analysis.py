"""
数据分析路由
包含总数据量、车型分布（饼图）、介质类型统计（柱状图）、省份数据统计（折线图）等分析接口
"""

import logging
import re

from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.dependencies import get_current_user, get_optional_user
from core.config import get_config as get_app_config
from statistics_service import get_dashboard_statistics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/analysis/total")
async def get_total_analysis(user: dict = Depends(get_current_user)):
    """获取总数据量统计"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]

                yc_pattern = re.compile(r'^\d{4}-\d{2}_yc$')
                monthly_tables = [t for t in tables if yc_pattern.match(t)]

                total_records = 0
                table_stats = []

                for table_name in monthly_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]

                    if count > 0:
                        total_records += count
                        year = table_name[:4]
                        month = table_name[5:7]
                        table_stats.append({
                            "table": table_name,
                            "count": count,
                            "label": f"{year}年{int(month):02d}月"
                        })

                table_stats.sort(key=lambda x: x['count'], reverse=True)

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "totalRecords": total_records,
                        "tableCount": len(table_stats),
                        "tables": table_stats
                    }
                }

    except Exception as e:
        logger.error(f"获取总数据量统计失败: {e}")
        return {"code": 500, "message": "获取总数据量统计失败"}


@router.get("/api/analysis/userAccessSource")
async def get_user_access_source(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """获取车型分布数据（饼图，前端期望 { name, value } 格式）"""
    try:
        data = get_dashboard_statistics()

        if data and data.get("vehicle_types"):
            vehicle_types = data["vehicle_types"]
            access_list = [
                {"name": item.get("type", "未知"), "value": item.get("count", 0)}
                for item in vehicle_types
            ]
            return {"code": 200, "message": "success", "data": access_list}

        return {"code": 200, "message": "success", "data": []}

    except Exception as e:
        logger.error(f"获取车型分布数据失败: {e}")
        return {"code": 500, "message": "获取车型分布数据失败"}


@router.get("/api/analysis/weeklyUserActivity")
async def get_weekly_user_activity(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """获取通行介质类型统计（柱状图，前端期望 { name, value } 格式）"""
    try:
        data = get_dashboard_statistics()

        if data and data.get("media_types"):
            media_types = data["media_types"]
            media_name_map = {
                "1": "ETC", "2": "CPC", "3": "纸券",
                "4": "OBU", "9": "其他"
            }
            activity_list = [
                {"name": media_name_map.get(item.get("type", ""), item.get("type", "未知")),
                 "value": item.get("count", 0)}
                for item in media_types
            ]
            return {"code": 200, "message": "success", "data": activity_list}

        return {"code": 200, "message": "success", "data": []}

    except Exception as e:
        logger.error(f"获取介质类型统计失败: {e}")
        return {"code": 500, "message": "获取介质类型统计失败"}


@router.get("/api/analysis/monthlySales")
async def get_monthly_sales(
    year: int = 2024,
    user: dict = Depends(get_current_user)
):
    """获取省份数据统计（折线图，前端期望 { name, estimate, actual } 格式）"""
    try:
        data = get_dashboard_statistics()

        if data and data.get("province_data"):
            province_data = data["province_data"]
            sales_list = [
                {
                    "name": item.get("province", "未知"),
                    "estimate": item.get("count", 0),
                    "actual": item.get("count", 0)
                }
                for item in province_data
            ]
            return {"code": 200, "message": "success", "data": sales_list}

        return {"code": 200, "message": "success", "data": []}

    except Exception as e:
        logger.error(f"获取省份数据统计失败: {e}")
        return {"code": 500, "message": "获取省份数据统计失败"}


@router.post("/api/analytics/route")
async def analytics_route(request: dict, user: dict | None = Depends(get_optional_user)):
    """通用分析路由：接收路由导航日志或执行自定义分析

    [路由导航日志] 标记段 - 如需移除路由日志功能，删除本函数中 route_log 分支
    使用可选认证：未登录用户也能正常访问页面，路由日志中 user_id 为 None
    """
    try:
        analysis_type = request.get('type', '')

        if analysis_type == 'custom':
            # 自定义分析需要认证
            if user is None:
                return {"code": 401, "message": "需要登录"}
            params = request.get('params', {})
            result = await execute_custom_analysis(params)
            return {
                "code": 200,
                "message": "success",
                "data": result
            }

        # [路由导航日志] 前端 permission.ts afterEach 发送的导航日志
        has_navigation_fields = 'from' in request or 'to' in request or 'timestamp' in request
        if has_navigation_fields:
            await _save_route_navigation_log(request, user)
            return {"code": 200, "message": "success"}

        return {"code": 400, "message": "不支持的分析类型"}

    except Exception as e:
        logger.error(f"执行分析失败: {e}")
        return {"code": 500, "message": "执行分析失败"}


# [路由导航日志] 标记段 - 如需移除路由日志功能，删除此函数
async def _save_route_navigation_log(request: dict, user: dict) -> None:
    """将前端路由导航日志写入 route_logs 表"""
    try:
        from core.models import RouteNavigationLog
        from database import get_db_connection

        log = RouteNavigationLog(**request)
        user_id = user.get('id') if isinstance(user, dict) else None

        config = get_app_config()
        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO route_logs
                       (user_id, from_path, to_path, duration_ms, user_agent, timestamp)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (user_id, log.from_path, log.to_path, log.duration, log.user_agent, log.timestamp)
                )
            conn.commit()
    except Exception as e:
        logger.warning(f"[路由导航日志] 保存失败: {e}")


async def execute_custom_analysis(params: dict) -> dict:
    """执行自定义分析逻辑"""
    return {
        "type": "custom",
        "params": params,
        "result": "自定义分析结果"
    }
