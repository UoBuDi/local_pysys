"""
定时任务调度器 — 基于 APScheduler 3.x
功能：
- 从数据库 scheduled_tasks 表自动发现并注册已启用的任务
- 支持完整的 5 字段 Cron 表达式
- 任务执行自动写入 task_execution_history 并更新 scheduled_tasks 状态
- 支持热更新（修改 Cron/启用状态后无需重启）
- 计算并更新 next_run_time
- cloud_portal_data_sync 使用 admin 绑定的云门户账号自动登录获取 Token
"""

import logging
from datetime import datetime
from time import time as now_timestamp

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from core.db import get_user_db_connection
from statistics_service import (
    run_statistics_task, update_task_status,
    start_task_execution, end_task_execution
)

logger = logging.getLogger(__name__)

# 全局调度器实例
_scheduler: BackgroundScheduler | None = None


# ==================== 任务执行函数注册表 ====================
# 新增任务只需在此注册执行函数，调度器会自动发现

TASK_REGISTRY: dict[str, callable] = {}


def register_task(task_name: str):
    """任务注册装饰器：将函数注册到 TASK_REGISTRY"""
    def decorator(func):
        TASK_REGISTRY[task_name] = func
        return func
    return decorator


@register_task('dashboard_statistics_daily')
def _run_dashboard_statistics():
    """执行 Dashboard 统计任务"""
    task_name = 'dashboard_statistics_daily'
    history_id = start_task_execution(task_name)
    start_ts = now_timestamp()

    try:
        result = run_statistics_task()
        status = 'success' if result['success'] else 'failed'
        message = result['message']
        duration = int(now_timestamp() - start_ts)
        end_task_execution(history_id, status, message, duration=duration)
        update_task_status(task_name, status, message)
        logger.info(f"任务 {task_name} 执行完成: {message}")
    except Exception as e:
        duration = int(now_timestamp() - start_ts)
        error_msg = f"执行异常: {str(e)}"
        end_task_execution(history_id, 'failed', error_msg, duration=duration)
        update_task_status(task_name, 'failed', error_msg)
        logger.error(f"任务 {task_name} 执行异常: {e}")


@register_task('cloud_portal_data_sync')
def _run_cloud_portal_data_sync():
    """执行云门户数据同步任务（自动登录获取 Token）"""
    task_name = 'cloud_portal_data_sync'
    history_id = start_task_execution(task_name)
    start_ts = now_timestamp()

    try:
        # 从 portal_accounts 表获取 admin(user_id=1) 绑定的云门户账号
        access_token = _get_cloud_portal_token_for_admin()

        if not access_token:
            message = '未找到 admin 绑定的云门户账号或自动登录失败，请先配置云门户账号'
            duration = int(now_timestamp() - start_ts)
            end_task_execution(history_id, 'failed', message, duration=duration)
            update_task_status(task_name, 'failed', message)
            logger.warning(f"任务 {task_name}: {message}")
            return

        # 使用 Token 执行数据同步
        from cloud_portal_data_service import run_cloud_portal_data_sync
        result = run_cloud_portal_data_sync(access_token)

        status = 'success' if result.get('success') else 'failed'
        message = result.get('message', '同步完成')
        duration = int(now_timestamp() - start_ts)
        end_task_execution(history_id, status, message, duration=duration)
        update_task_status(task_name, status, message)
        logger.info(f"任务 {task_name} 执行完成: {message}")

    except Exception as e:
        duration = int(now_timestamp() - start_ts)
        error_msg = f"执行异常: {str(e)}"
        end_task_execution(history_id, 'failed', error_msg, duration=duration)
        update_task_status(task_name, 'failed', error_msg)
        logger.error(f"任务 {task_name} 执行异常: {e}")


def _get_cloud_portal_token_for_admin() -> str:
    """获取 admin 用户绑定的云门户 Token，如果 Token 过期则自动重登录"""
    try:
        from routers.cloud_portal import _get_account, _is_token_valid, _auto_relogin

        # admin 用户的 user_id 为 1
        account = _get_account(1)
        if not account:
            logger.warning("admin 未绑定云门户账号")
            return ""

        # 检查 Token 是否有效
        if _is_token_valid(account):
            return account.get('access_token', '')

        # Token 过期，尝试自动重登录
        logger.info("admin 云门户 Token 已过期，尝试自动重登录...")
        relogin_result = _auto_relogin(1)
        if relogin_result.get('success'):
            return relogin_result['data'].get('access_token', '')
        else:
            logger.error(f"admin 自动重登录失败: {relogin_result.get('message')}")
            return ""

    except Exception as e:
        logger.error(f"获取 admin 云门户 Token 失败: {e}")
        return ""


# ==================== 调度器管理 ====================


def _update_next_run_time(task_name: str):
    """从 APScheduler 获取任务的下次执行时间并更新到数据库"""
    if not _scheduler or not _scheduler.running:
        return

    try:
        job = _scheduler.get_job(task_name)
        if job:
            next_time = job.next_run_time
            conn = get_user_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE scheduled_tasks SET next_run_time = %s WHERE task_name = %s",
                        (next_time.strftime('%Y-%m-%d %H:%M:%S') if next_time else None, task_name)
                    )
                    conn.commit()
            finally:
                conn.close()
    except Exception as e:
        logger.warning(f"更新 next_run_time 失败: {e}")


def _update_all_next_run_times():
    """更新所有已注册任务的 next_run_time"""
    if not _scheduler or not _scheduler.running:
        return

    conn = get_user_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT task_name FROM scheduled_tasks WHERE is_enabled = 1")
            tasks = cursor.fetchall()
        for task in tasks:
            _update_next_run_time(task['task_name'])
    finally:
        conn.close()


def _load_and_register_tasks():
    """从数据库加载已启用的任务并注册到调度器"""
    conn = get_user_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT task_name, cron_expression, is_enabled FROM scheduled_tasks"
            )
            tasks = cursor.fetchall()

        for task in tasks:
            task_name = task['task_name']
            cron_expr = task['cron_expression']
            is_enabled = task.get('is_enabled', 0)

            if is_enabled != 1:
                # 禁用的任务：如果调度器中存在则移除
                if _scheduler and _scheduler.get_job(task_name):
                    _scheduler.remove_job(task_name)
                    logger.info(f"已移除禁用任务: {task_name}")
                continue

            # 检查是否有注册的执行函数
            if task_name not in TASK_REGISTRY:
                logger.warning(f"任务 {task_name} 无注册执行函数，跳过")
                continue

            if not cron_expr:
                logger.warning(f"任务 {task_name} 无 Cron 表达式，跳过")
                continue

            # 解析 Cron 表达式并注册/更新任务
            try:
                parts = cron_expr.strip().split()
                if len(parts) != 5:
                    logger.warning(f"任务 {task_name} 的 Cron 表达式格式错误: {cron_expr}")
                    continue

                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )

                existing_job = _scheduler.get_job(task_name) if _scheduler else None

                if existing_job:
                    existing_trigger = existing_job.trigger
                    if existing_trigger != trigger:
                        _scheduler.reschedule_job(task_name, trigger=trigger)
                        logger.info(f"已更新任务调度: {task_name}, Cron: {cron_expr}")
                else:
                    _scheduler.add_job(
                        TASK_REGISTRY[task_name],
                        trigger=trigger,
                        id=task_name,
                        name=task_name,
                        replace_existing=True
                    )
                    logger.info(f"已注册定时任务: {task_name}, Cron: {cron_expr}")

            except Exception as e:
                logger.error(f"注册任务 {task_name} 失败: {e}")

    finally:
        conn.close()


def start_scheduler():
    """启动调度器"""
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.warning("定时任务调度器已在运行")
        return

    _scheduler = BackgroundScheduler(
        job_defaults={'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 300}
    )

    # 先注册任务（此时 next_run_time 尚未计算）
    _load_and_register_tasks()

    # 启动调度器，此后 Job 才有 next_run_time
    _scheduler.start()
    logger.info("定时任务调度器已启动（APScheduler）")

    # 启动后统一更新所有任务的 next_run_time
    _update_all_next_run_times()


def stop_scheduler():
    """停止调度器"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已停止")


def reload_tasks():
    """热更新：重新从数据库加载任务配置并刷新调度器"""
    if not _scheduler or not _scheduler.running:
        logger.warning("调度器未运行，无法热更新")
        return

    _load_and_register_tasks()
    _update_all_next_run_times()
    logger.info("定时任务配置已热更新")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    start_scheduler()

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
        print("调度器已停止")
