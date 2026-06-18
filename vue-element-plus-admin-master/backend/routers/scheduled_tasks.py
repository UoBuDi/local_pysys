"""
定时任务与Dashboard统计路由
包含：Dashboard统计数据查询、定时任务管理、任务执行历史查询
"""

import logging
import json
import threading
from datetime import datetime
from time import time as now_timestamp

from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.dependencies import get_current_user
from core.db import get_user_db_connection
from statistics_service import (
    get_dashboard_statistics, run_statistics_task, update_task_status,
    start_task_execution, end_task_execution, get_consecutive_failures
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 内存中的任务执行状态跟踪（用于异步执行轮询）
_task_run_status = {}


@router.get("/api/dashboard-statistics/")
async def get_dashboard_statistics_api(
    stat_month: Optional[str] = Query(default=None, description="统计月份，格式 YYYY-MM"),
    user: dict = Depends(get_current_user)
):
    """获取Dashboard统计数据，支持按月份查询"""
    try:
        data = get_dashboard_statistics(stat_month=stat_month)
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
                    "id": None, "stat_date": "", "stat_month": "",
                    "total_transactions": 0, "free_transactions": 0,
                    "split_section_amount": 0, "total_amount": 0,
                    "total_split_amount": 0, "station_count": 0,
                    "vehicle_types": [], "media_types": [],
                    "province_data": [], "daily_transactions": []
                }
            }
    except Exception as e:
        logger.error(f"获取Dashboard统计数据失败: {e}")
        return {"code": 500, "message": f"获取统计数据失败: {str(e)}"}


@router.get("/api/scheduled-tasks/")
async def get_scheduled_tasks_api(user: dict = Depends(get_current_user)):
    """获取所有定时任务列表，包含描述和连续失败次数"""
    conn = None
    try:
        conn = get_user_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM scheduled_tasks ORDER BY id")
            tasks = cursor.fetchall()

            result = []
            for t in tasks:
                # 从 config JSON 中提取 description
                config_str = t.get("config")
                description = ""
                if config_str:
                    try:
                        config_data = json.loads(config_str) if isinstance(config_str, str) else config_str
                        description = config_data.get("description", "")
                    except (json.JSONDecodeError, AttributeError):
                        pass

                # 查询连续失败次数
                consecutive_failures = get_consecutive_failures(t.get("task_name"))

                result.append({
                    "id": t.get("id"),
                    "task_name": t.get("task_name"),
                    "task_type": t.get("task_type"),
                    "cron_expression": t.get("cron_expression"),
                    "description": description,
                    "is_enabled": t.get("is_enabled", 0),
                    "last_run_time": str(t.get("last_run_time", "")) if t.get("last_run_time") else None,
                    "next_run_time": str(t.get("next_run_time", "")) if t.get("next_run_time") else None,
                    "last_run_status": t.get("last_run_status"),
                    "last_run_message": t.get("last_run_message"),
                    "consecutive_failures": consecutive_failures,
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
    """更新定时任务配置，更新后自动热刷新调度器"""
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

            # 热更新调度器
            try:
                from scheduler import reload_tasks
                reload_tasks()
            except Exception as e:
                logger.warning(f"热更新调度器失败: {e}")

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


def _execute_task_async(task_name: str, run_id: str):
    """在后台线程中执行任务，更新内存状态和数据库记录"""
    history_id = start_task_execution(task_name)
    start_ts = now_timestamp()

    try:
        _task_run_status[run_id] = {"status": "running", "message": "任务执行中..."}

        if task_name == "dashboard_statistics_daily":
            result = run_statistics_task()
            status = "success" if result["success"] else "failed"
            message = result["message"]
            update_task_status(task_name, status, message)
        elif task_name == "cloud_portal_data_sync":
            # 手动执行也使用 admin 自动登录
            from scheduler import _get_cloud_portal_token_for_admin
            access_token = _get_cloud_portal_token_for_admin()
            if access_token:
                from cloud_portal_data_service import run_cloud_portal_data_sync
                result = run_cloud_portal_data_sync(access_token)
                status = "success" if result.get("success") else "failed"
                message = result.get("message", "同步完成")
                update_task_status(task_name, status, message)
            else:
                status = "failed"
                message = "未找到 admin 绑定的云门户账号或自动登录失败"
                update_task_status(task_name, status, message)
        else:
            status = "failed"
            message = f"不支持的任务: {task_name}"

        duration = int(now_timestamp() - start_ts)
        end_task_execution(history_id, status, message, duration=duration)

        _task_run_status[run_id] = {
            "status": status,
            "message": message,
            "duration": duration,
            "completed_at": datetime.now().isoformat()
        }

    except Exception as e:
        duration = int(now_timestamp() - start_ts)
        error_msg = f"执行任务异常: {str(e)}"
        end_task_execution(history_id, "failed", error_msg, duration=duration)
        update_task_status(task_name, "failed", error_msg)

        _task_run_status[run_id] = {
            "status": "failed",
            "message": error_msg,
            "duration": duration,
            "completed_at": datetime.now().isoformat()
        }


@router.post("/api/scheduled-tasks/{task_name}/run")
async def run_scheduled_task_api(
    task_name: str,
    user: dict = Depends(get_current_user)
):
    """手动执行定时任务（异步），立即返回 run_id 用于轮询状态"""
    try:
        run_id = f"{task_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        thread = threading.Thread(
            target=_execute_task_async,
            args=(task_name, run_id),
            daemon=True
        )
        thread.start()

        return {
            "code": 200,
            "message": "任务已提交执行",
            "data": {
                "run_id": run_id,
                "task_name": task_name,
                "status": "running"
            }
        }
    except Exception as e:
        logger.error(f"提交定时任务执行失败: {e}")
        return {"code": 500, "message": f"提交任务执行失败: {str(e)}"}


@router.get("/api/scheduled-tasks/run-status/{run_id}")
async def get_task_run_status_api(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    """查询异步任务执行状态"""
    status_info = _task_run_status.get(run_id)
    if not status_info:
        return {"code": 404, "message": "运行记录不存在或已过期"}

    return {"code": 200, "message": "success", "data": status_info}


@router.get("/api/task-execution-history/")
async def get_task_execution_history_api(
    task_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    user: dict = Depends(get_current_user)
):
    """获取任务执行历史（分页）"""
    conn = None
    try:
        conn = get_user_db_connection()
        with conn.cursor() as cursor:
            where_clause = "WHERE task_name = %s" if task_name else ""
            params_count = [task_name] if task_name else []
            params_data = [task_name] if task_name else []

            count_sql = f"SELECT COUNT(*) as total FROM task_execution_history {where_clause}"
            cursor.execute(count_sql, params_count)
            total = cursor.fetchone()["total"]

            offset = (page - 1) * page_size
            params_data.extend([page_size, offset])

            data_sql = f"""
                SELECT id, task_name, start_time, end_time, status, message,
                       details, duration_seconds, created_at
                FROM task_execution_history
                {where_clause}
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, params_data)
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

            return {
                "code": 200,
                "message": "success",
                "data": {
                    "list": result,
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
    except Exception as e:
        logger.error(f"获取任务执行历史失败: {e}")
        return {"code": 500, "message": f"获取执行历史失败: {str(e)}"}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
