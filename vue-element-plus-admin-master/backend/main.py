"""
FastAPI 应用主入口文件
模块化重构后的主文件，负责：
- 应用初始化（FastAPI 实例、中间件、静态文件）
- 注册所有路由模块
- 启动/关闭事件处理
- 全局异常处理器
"""

import os
import logging

from fastapi import FastAPI, Request, HTTPException, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn

# 配置日志系统
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

# 清除默认处理器并重新配置
logger.handlers.clear()

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'app.log'),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

error_handler = RotatingFileHandler(
    os.path.join(log_dir, 'error.log'),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)
logger.addHandler(error_handler)

logging.getLogger('asyncio').setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI()

# 添加 CORS 中间件（允许跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加 GZip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ==================== 注册路由模块 ====================

# 认证相关路由
from routers.auth import router as auth_router
app.include_router(auth_router)

# 用户管理路由
from routers.users import router as users_router
app.include_router(users_router)

# 角色管理路由
from routers.roles import router as roles_router
app.include_router(roles_router)

# 菜单管理路由
from routers.menus import router as menus_router
app.include_router(menus_router)

# 部门管理路由
from routers.departments import router as departments_router
app.include_router(departments_router)

# 权限管理路由
from routers.permissions import router as permissions_router
app.include_router(permissions_router)

# 关联分配路由
from routers.assignments import router as assignments_router
app.include_router(assignments_router)

# 同步管理路由
from routers.sync import router as sync_router
app.include_router(sync_router)

# 配置管理路由
from routers.config import router as config_router
app.include_router(config_router)

# 数据分析路由
from routers.analysis import router as analysis_router
app.include_router(analysis_router)

# 拆分匹配路由
from routers.split_match import router as split_match_router
app.include_router(split_match_router)

# 详单查询路由
from routers.detail_query import router as detail_query_router
app.include_router(detail_query_router)

# 路径匹配路由
from routers.path_match import router as path_match_router
app.include_router(path_match_router)

# WebSocket 端点路由
from routers.websocket_endpoints import router as websocket_router
app.include_router(websocket_router)

# 健康检查路由
from routers.health import router as health_router
app.include_router(health_router)

# 定时任务与Dashboard统计路由
from routers.scheduled_tasks import router as scheduled_tasks_router
app.include_router(scheduled_tasks_router)

# 云门户路由
from routers.cloud_portal import router as cloud_portal_router
app.include_router(cloud_portal_router)

from routers.chat import router as chat_router
app.include_router(chat_router)

# WebSocket 双协议配置路由
from routers.ws_config import router as ws_config_router
app.include_router(ws_config_router)

# 追查详单路由
from routers.investigation import router as investigation_router
app.include_router(investigation_router)

# 系统通知与管控路由
from routers.notifications import router as notifications_router
app.include_router(notifications_router)


# ==================== 静态文件服务 ====================

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # 后端专用静态资源（如 chat_files）
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 前端构建产物的静态资源挂载
    # index.html 中引用的路径为 /assets/js/...、/assets/css/...、/favicon.ico、/logo.png
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")
else:
    logger.warning(f"静态文件目录不存在: {static_dir}")


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行初始化操作"""
    logger.info("========================================")
    logger.info("FastAPI 应用正在启动...")
    logger.info("========================================")
    
    try:
        # 初始化数据库连接池
        from database import create_db_pool
        
        config = None
        try:
            from core.config import get_config as get_app_config
            config = get_app_config()
        except Exception:
            from config import load_config
            config = load_config()
        
        if config:
            from database import create_db_pool
            create_db_pool(config)
            logger.info("数据库连接池初始化完成")
        else:
            logger.warning("无法加载配置文件，跳过连接池初始化")
        
        # 启动定时任务调度器
        try:
            from scheduler import start_scheduler
            start_scheduler()
            logger.info("定时任务调度器已启动")
        except Exception as e:
            logger.warning(f"启动定时任务调度器失败: {e}")

        # 初始化云门户数据服务（延迟初始化策略）
        try:
            from cloud_portal_data_service import CloudPortalDataService
            app.state.cloud_portal_service = None
            logger.info("云门户数据服务模块已加载（延迟初始化）")
        except Exception as e:
            logger.warning(f"加载云门户数据服务模块失败: {e}")
            app.state.cloud_portal_service = None

        # [路由导航日志] 自动建表 - 如需移除路由日志功能，删除此段
        try:
            from init_route_logs_table import init_route_logs_table
            init_route_logs_table(config)
        except Exception as e:
            logger.warning(f"[路由导航日志] 表初始化失败: {e}")

        # 初始化聊天表（chat_messages + chat_sessions）
        try:
            from database import get_db_connection
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    # CH-04: 图片消息支持 + CH-03: 撤回 + CH-08: @提及
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS chat_messages (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            room_id VARCHAR(100) NOT NULL,
                            sender_id INT NOT NULL,
                            sender_name VARCHAR(100),
                            content_type VARCHAR(20) NOT NULL DEFAULT 'text',
                            content TEXT NOT NULL,
                            is_recalled TINYINT NOT NULL DEFAULT 0 COMMENT '是否已撤回',
                            mentioned_user_ids JSON DEFAULT NULL COMMENT '@提及用户ID列表',
                            file_name VARCHAR(500) DEFAULT NULL COMMENT '文件原始名',
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_room_created (room_id, created_at),
                            INDEX idx_sender (sender_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    # CH-07: 置顶/免打扰
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS chat_sessions (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            user_id INT NOT NULL,
                            room_id VARCHAR(100) NOT NULL,
                            room_name VARCHAR(200) DEFAULT NULL,
                            room_type VARCHAR(20) NOT NULL DEFAULT 'private',
                            last_message_id BIGINT DEFAULT NULL,
                            unread_count INT DEFAULT 0,
                            is_pinned TINYINT NOT NULL DEFAULT 0 COMMENT '是否置顶',
                            is_muted TINYINT NOT NULL DEFAULT 0 COMMENT '是否免打扰',
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            UNIQUE KEY uk_user_room (user_id, room_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    # CH-02: 群聊成员表
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS chat_group_members (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            room_id VARCHAR(100) NOT NULL,
                            user_id INT NOT NULL,
                            role VARCHAR(20) NOT NULL DEFAULT 'member',
                            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE KEY uk_room_user (room_id, user_id),
                            INDEX idx_room_id (room_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    # CH-05: 消息已读记录表
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS chat_message_read (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            message_id BIGINT NOT NULL,
                            user_id INT NOT NULL,
                            read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE KEY uk_msg_user (message_id, user_id),
                            INDEX idx_message_id (message_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    # 为旧表补充新字段（MySQL 8.0 不支持 ADD COLUMN IF NOT EXISTS，需先查 INFORMATION_SCHEMA）
                    alter_columns = [
                        ("chat_messages", "is_recalled", "TINYINT NOT NULL DEFAULT 0 COMMENT '是否已撤回'"),
                        ("chat_messages", "mentioned_user_ids", "JSON DEFAULT NULL COMMENT '@提及用户ID列表'"),
                        ("chat_messages", "file_name", "VARCHAR(500) DEFAULT NULL COMMENT '文件原始名'"),
                        ("chat_sessions", "is_pinned", "TINYINT NOT NULL DEFAULT 0 COMMENT '是否置顶'"),
                        ("chat_sessions", "is_muted", "TINYINT NOT NULL DEFAULT 0 COMMENT '是否免打扰'"),
                    ]
                    for table, column, definition in alter_columns:
                        try:
                            cursor.execute(
                                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
                                (table, column)
                            )
                            if not cursor.fetchone():
                                cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
                                logger.info(f"已为 {table} 表添加 {column} 列")
                        except Exception as e:
                            logger.warning(f"为 {table} 添加 {column} 列失败: {e}")
                    conn.commit()
            logger.info("聊天表(chat_messages/chat_sessions/chat_group_members/chat_message_read)初始化完成")
        except Exception as e:
            logger.warning(f"初始化聊天表失败（非致命）: {e}")

        # F-01: 乐观锁版本管理表 + F-05: 编辑历史表 + F-11: 通知表
        try:
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    # F-01: 行版本管理表（乐观锁）
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS row_versions (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            table_name VARCHAR(100) NOT NULL COMMENT '月度表名',
                            row_id VARCHAR(100) NOT NULL COMMENT '通行标识ID',
                            version INT NOT NULL DEFAULT 1 COMMENT '乐观锁版本号',
                            updated_by VARCHAR(100) DEFAULT NULL COMMENT '最后修改者',
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            UNIQUE KEY uk_table_row (table_name, row_id),
                            INDEX idx_table_name (table_name),
                            INDEX idx_updated_at (updated_at)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行版本管理表（乐观锁）'
                    """)
                    # F-05: 编辑历史记录表
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS edit_history (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            table_name VARCHAR(100) NOT NULL,
                            row_id VARCHAR(100) NOT NULL,
                            user_id INT NOT NULL,
                            username VARCHAR(100) NOT NULL,
                            action VARCHAR(20) NOT NULL DEFAULT 'update' COMMENT 'update/import/force_overwrite',
                            version_before INT DEFAULT NULL,
                            version_after INT DEFAULT NULL,
                            changed_fields JSON DEFAULT NULL COMMENT '{"field": {"old": "x", "new": "y"}}',
                            force_overwrite TINYINT(1) DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_table_row (table_name, row_id),
                            INDEX idx_user (user_id),
                            INDEX idx_created_at (created_at)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='编辑历史记录'
                    """)
                    # F-11: 系统通知表
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS notifications (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            type VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT 'system/approval/alert',
                            title VARCHAR(200) NOT NULL,
                            content TEXT,
                            sender_id INT DEFAULT NULL,
                            target_type VARCHAR(20) DEFAULT 'all' COMMENT 'all/user/role/department',
                            target_ids JSON DEFAULT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统通知'
                    """)
                    # 启动时自动清理过期数据
                    try:
                        cursor.execute("DELETE FROM edit_history WHERE created_at < NOW() - INTERVAL 90 DAY")
                        cursor.execute("DELETE FROM notifications WHERE created_at < NOW() - INTERVAL 30 DAY")
                    except Exception:
                        pass
                    conn.commit()
            logger.info("版本表(row_versions)/编辑历史表(edit_history)/通知表(notifications)初始化完成")
        except Exception as e:
            logger.warning(f"初始化编辑历史/通知表失败（非致命）: {e}")

        logger.info("========================================")
        logger.info("FastAPI 应用启动完成！")
        logger.info("========================================")
        
    except Exception as e:
        logger.error(f"应用启动过程中发生错误: {e}", exc_info=True)


# ==================== 关闭事件 ====================

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("========================================")
    logger.info("FastAPI 应用正在关闭...")
    logger.info("========================================")
    
    try:
        # 关闭数据库连接池
        from database import close_all_pools
        close_all_pools()
        logger.info("数据库连接池已关闭")
        
        # 停止后台任务
        try:
            from statistics_service import stop_all_tasks
            stop_all_tasks()
            logger.info("后台任务已停止")
        except Exception:
            pass

        # 停止定时任务调度器
        try:
            from scheduler import stop_scheduler
            stop_scheduler()
            logger.info("定时任务调度器已停止")
        except Exception:
            pass
        
        # 停止同步服务
        try:
            from sync_service import stop_sync
            stop_sync()
            logger.info("同步服务已停止")
        except Exception:
            pass
        
        logger.info("========================================")
        logger.info("FastAPI 应用已安全关闭")
        logger.info("========================================")
        
    except Exception as e:
        logger.error(f"应用关闭过程中发生错误: {e}", exc_info=True)


# ==================== 全局异常处理器 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "请求参数验证失败",
            "data": {
                "errors": errors
            }
        }
    )


@app.exception_handler(WebSocketDisconnect)
async def websocket_disconnect_exception_handler(request: Request, exc: WebSocketDisconnect):
    """WebSocket 断开连接异常处理器"""
    logger.debug(f"WebSocket 连接断开: code={exc.code}, reason={exc.reason}")
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": f"WebSocket 连接断开: {exc.reason or 'Unknown reason'}",
            "data": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器（捕获所有未处理的异常）"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }
    )


# SPA 前端路由 fallback：所有非 API、非 static 的 GET 请求返回 index.html
# Vue Router 使用 history 模式，需要服务端将前端路由交由 index.html 处理
static_index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
if os.path.exists(static_index_path):
    @app.get("/")
    async def root():
        """根路径返回静态首页"""
        return FileResponse(static_index_path)

    # 前端入口文件引用的根级静态资源
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = os.path.join(static_dir, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        raise HTTPException(status_code=404)

    @app.get("/logo.png")
    async def logo():
        logo_path = os.path.join(static_dir, "logo.png")
        if os.path.exists(logo_path):
            return FileResponse(logo_path)
        raise HTTPException(status_code=404)

    @app.get("/{path:path}")
    async def spa_fallback(request: Request, path: str):
        """SPA 路由 fallback：非 API、非静态资源的请求返回 index.html"""
        # API 请求和静态资源路径不拦截
        if path.startswith("api/") or path.startswith("static/") or path.startswith("assets/"):
            raise HTTPException(status_code=404)
        # 带文件扩展名的请求（如 .js、.css、.png）不拦截
        if "." in path.split("/")[-1]:
            raise HTTPException(status_code=404)
        return FileResponse(static_index_path)


# 主程序入口
if __name__ == "__main__":
    print("=" * 50)
    print("FastAPI 后端服务器启动中...")
    print(f"监听地址: http://0.0.0.0:8001")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
