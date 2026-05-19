"""
[路由导航日志] 自动建表模块
用途：存储前端路由跳转追踪数据，用于用户行为分析
标记：如需移除路由导航日志功能，删除本文件及 routers/analysis.py 中 ROUTE_LOG 标记段
"""

import pymysql
import logging

logger = logging.getLogger(__name__)

ROUTE_LOGS_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS route_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id INT DEFAULT NULL COMMENT '用户ID',
    from_path VARCHAR(255) DEFAULT NULL COMMENT '来源路由路径',
    to_path VARCHAR(255) DEFAULT NULL COMMENT '目标路由路径',
    duration_ms INT DEFAULT NULL COMMENT '导航耗时(毫秒)',
    user_agent VARCHAR(512) DEFAULT NULL COMMENT '浏览器UA',
    timestamp BIGINT DEFAULT NULL COMMENT '前端时间戳',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '服务器记录时间',
    INDEX idx_route_logs_user (user_id),
    INDEX idx_route_logs_to_path (to_path),
    INDEX idx_route_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='[路由导航日志] 前端路由跳转追踪'
"""


def init_route_logs_table(config) -> bool:
    """初始化 route_logs 表，应用启动时调用"""
    try:
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(ROUTE_LOGS_CREATE_SQL)
            conn.commit()

        logger.info("[路由导航日志] route_logs 表初始化完成")
        return True
    except Exception as e:
        logger.warning(f"[路由导航日志] route_logs 表初始化失败: {e}")
        return False
