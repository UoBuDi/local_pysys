"""
定时任务与Dashboard统计路由
包含：Dashboard统计数据查询、定时任务管理、任务执行历史查询
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.dependencies import get_current_user
from statistics_service import get_dashboard_statistics, run_statistics_task, update_task_status, get_user_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/dashboard-statistics/")
async def get_dashboard_statistics_api(user: dict = Depends(get_current_user)):
    """获取Dashboard统计数据（最新一条）"""
    try:
        data = get_dashboard_statistics()
        if data:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "id": data.get("id"),
                    "stat_date": str(data.get("stat_date", "")),
                    "stat_month": data.get("stat_month", ""),
                    "total_transactions": data.get("total_transactions", 0),
                    "free_transactions": data.get("free_transactions", 0),
                    "split_section_amount": float(data.get("split_section_amount", 0) or 0),
                    "total_amount": float(data.get("total_amount", 0) or 0),
                    "total_split_amount": float(data.get("split_section_amount", 0) or 0),
                    "station_count": data.get("station_count", 0),
                    "vehicle_types": data.get("vehicle_types", []),
                    "media_types": data.get("media_types", []),
                    "province_data": data.get("province_data", []),
                    "daily_transactions": data.get("daily_transactions", []),
                    "created_at": str(data.get("created_at", "")),
                    "updated_at": str(data.get("updated_at", ""))
                }
            }
        else:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "id": None,
                    "stat_date": "",
                    "stat_month": "",
                    "total_transactions": 0,
                    "free_transactions": 0,
                    "split_section_amount": 0,
                    "total_amount": 0,
                    "total_split_amount": 0,
                    "station_count": 0,
                    "vehicle_types": [],
                    "media_types": [],
                    "province_data": [],
                    "daily_transactions": []
                }
            }
    except Exception as e:
        logger.error(f"获取Dashboard统计数据失败: {e}")
        return {"code": 500, "message": f"获取统计数据失败: {str(e)}"}


@router.get("/api/scheduled-tasks/")
async def get_scheduled_tasks_api(user: dict = Depends(get_current_user)):
    """获取所有定时任务列表"""
    conn = None
    try:
        conn = get_user_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM scheduled_tasks ORDER BY id")
            tasks = cursor.fetchall()

            result = []
            for t in tasks:
                result.append({
                    "id": t.get("id"),
                    "task_name": t.get("task_name"),
                    "task_type": t.get("task_type"),
                    "cron_expression": t.get("cron_expression"),
                    "is_enabled": t.get("is_enabled", 0),
                    "last_run_time": str(t.get("last_run_time", "")) if t.get("last_run_time") else None,
                    "next_run_time": str(t.get("next_run_time", "")) if t.get("next_run_time") else None,
                    "last_run_status": t.get("last_run_status"),
                    "last_run_message": t.get("last_run_message"),
                    "created_at": str(t.get("created_at", "")) if t.get("created_at") else None,
                    "updated_at": str(t.get("updated_at", "")) if t.get("updated_at") else None
                })

            return {"code": 200, "message": "success", "data": result}
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        return {"code": 500, "message": f"获取定时任务列表失败: {str(e)}"}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.put("/api/scheduled-tasks/{task_id}")
async def update_scheduled_task_api(
    task_id: int,
    data: dict,
    user: dict = Depends(get_current_user)
):
    """更新定时任务配置"""
    conn = None
    try:
        conn = get_user_db_connection()
        with conn.cursor() as cursor:
            updates = []
            params = []

            if "is_enabled" in data:
                updates.append("is_enabled = %s")
                params.append(data["is_enabled"])
            if "cron_expression" in data:
                updates.append("cron_expression = %s")
                params.append(data["cron_expression"])

            if not updates:
                return {"code": 400, "message": "没有需要更新的字段"}

            params.append(task_id)
            sql = f"UPDATE scheduled_tasks SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(sql, params)
            conn.commit()

            return {"code": 200, "message": "更新成功"}
    except Exception as e:
        logger.error(f"更新定时任务失败: {e}")
        if conn:
            conn.rollback()
        return {"code": 500, "message": f"更新定时任务失败: {str(e)}"}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/api/scheduled-tasks/{task_name}/run")
async def run_scheduled_task_api(
    task_name: str,
    user: dict = Depends(get_current_user)
):
    """手动执行定时任务"""
    try:
        if task_name == "dashboard_statistics_daily":
            result = run_statistics_task()
            status = "success" if result["success"] else "failed"
            update_task_status(task_name, status, result["message"])
            return {
                "code": 200,
                "message": result["message"],
                "data": {
                    "success": result["success"],
                    "message": result["message"],
                    "executed_at": result.get("executed_at", datetime.now().isoformat())
                }
            }
        else:
            return {"code": 400, "message": f"不支持的任务: {task_name}"}
    except Exception as e:
        logger.error(f"执行定时任务失败: {e}")
        return {"code": 500, "message": f"执行任务失败: {str(e)}"}


@router.get("/api/task-execution-history/")
async def get_task_execution_history_api(
    task_name: Optional[str] = Query(None),
    limit: int = Query(20),
    user: dict = Depends(get_current_user)
):
    """获取任务执行历史"""
    conn = None
    try:
        conn = get_user_db_connection()
        with conn.cursor() as cursor:
            if task_name:
                cursor.execute(
                    "SELECT * FROM task_execution_history WHERE task_name = %s ORDER BY created_at DESC LIMIT %s",
                    (task_name, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM task_execution_history ORDER BY created_at DESC LIMIT %s",
                    (limit,)
                )
            history = cursor.fetchall()

            result = []
            for h in history:
                result.append({
                    "id": h.get("id"),
                    "task_name": h.get("task_name"),
                    "start_time": str(h.get("start_time", "")) if h.get("start_time") else None,
                    "end_time": str(h.get("end_time", "")) if h.get("end_time") else None,
                    "status": h.get("status"),
                    "message": h.get("message"),
                    "details": h.get("details"),
                    "duration_seconds": h.get("duration_seconds"),
                    "created_at": str(h.get("created_at", "")) if h.get("created_at") else None
                })

            return {"code": 200, "message": "success", "data": result}
    except Exception as e:
        logger.error(f"获取任务执行历史失败: {e}")
        return {"code": 500, "message": f"获取执行历史失败: {str(e)}"}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
