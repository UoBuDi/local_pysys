"""
WebSocket 双协议(ws/wss)配置管理路由
提供公共无鉴权接口获取连接配置，以及管理员修改配置的接口
支持协议切换后广播通知所有在线客户端重连
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.config import get_config as get_app_config
from core.config import save_config_to_file, update_global_config
from core.dependencies import get_current_user
from core.ws_manager_instance import status_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class WsConfigRequest(BaseModel):
    """WebSocket 配置更新请求体"""
    protocol: str = Field(..., description="协议类型: ws 或 wss", pattern="^(ws|wss)$")
    host: Optional[str] = Field(None, description="WebSocket 服务地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="WebSocket 端口")
    ssl_cert_path: Optional[str] = Field(None, description="SSL证书路径（wss时必填）")
    ssl_key_path: Optional[str] = Field(None, description="SSL私钥路径（wss时必填）")


@router.get("/api/ws/config")
async def get_ws_config():
    """公共无鉴权接口：返回当前 WebSocket 连接配置（含完整URL）

    前端在建立 WebSocket 连接前调用此接口获取服务端配置，
    禁止前端硬编码协议、域名、端口。
    """
    try:
        config = get_app_config()
        protocol = config.get('WEBSOCKET', 'protocol', fallback='ws')
        host = config.get('WEBSOCKET', 'host', fallback='localhost')
        port = config.get('WEBSOCKET', 'port', fallback='8001')

        # 校验 protocol 合法性，防止配置文件被篡改
        if protocol not in ('ws', 'wss'):
            protocol = 'ws'
            logger.warning(f"config.ini 中 WEBSOCKET.protocol 值非法 '{protocol}'，回退为 ws")

        return {
            "code": 200,
            "message": "success",
            "data": {
                "protocol": protocol,
                "host": host,
                "port": int(port),
                "url": f"{protocol}://{host}:{port}/ws/status/frontend/"
            }
        }
    except Exception as e:
        logger.error(f"获取 WebSocket 配置失败: {e}")
        # 返回默认配置确保前端可降级使用
        return {
            "code": 200,
            "message": "使用默认配置",
            "data": {
                "protocol": "ws",
                "host": "localhost",
                "port": 8001,
                "url": "ws://localhost:8001/ws/status/frontend/"
            }
        }


@router.post("/api/ws/config")
async def update_ws_config(request: WsConfigRequest, user: dict = Depends(get_current_user)):
    """管理员更新 WebSocket 协议配置（需登录鉴权）

    更新 config.ini 的 [WEBSOCKET] 节，保存后立即生效，
    同时向所有在线客户端广播 protocol_changed 事件，
    客户端收到后会自动断开并用新配置重连。

    权限：所有已登录用户均可修改（后续可扩展为仅管理员）
    """
    try:
        config = get_app_config()

        # 确保 [WEBSOCKET] 节存在
        if not config.has_section('WEBSOCKET'):
            config.add_section('WEBSOCKET')

        # 写入各项配置（仅传入非 None 的字段）
        config.set('WEBSOCKET', 'protocol', request.protocol)

        if request.host is not None:
            config.set('WEBSOCKET', 'host', request.host)
        if request.port is not None:
            config.set('WEBSOCKET', 'port', str(request.port))
        if request.ssl_cert_path is not None:
            config.set('WEBSOCKET', 'ssl_cert_path', request.ssl_cert_path)
        if request.ssl_key_path is not None:
            config.set('WEBSOCKET', 'ssl_key_path', request.ssl_key_path)

        # 持久化到文件
        save_result = save_config_to_file(config)
        if not save_result:
            return {"code": 500, "message": "配置文件写入失败"}

        # 刷新内存中的全局配置对象
        update_global_config(config)

        new_protocol = request.protocol
        new_host = request.host or config.get('WEBSOCKET', 'host', fallback='localhost')
        new_port = request.port or int(config.get('WEBSOCKET', 'port', fallback='8001'))

        logger.info(f"WebSocket 配置已更新: protocol={new_protocol} host={new_host} port={new_port} operator={user.get('username')}")

        # 向所有在线客户端广播协议变更事件
        await status_manager.broadcast_all(
            status_manager.build_message(
                msg_type="protocol_changed",
                data={
                    "new_protocol": new_protocol,
                    "new_host": new_host,
                    "new_port": new_port,
                    "url": f"{new_protocol}://{new_host}:{new_port}/ws/status/frontend/"
                }
            )
        )

        return {
            "code": 200,
            "message": "配置已更新，正在通知客户端重连",
            "data": {
                "protocol": new_protocol,
                "host": new_host,
                "port": new_port,
                "url": f"{new_protocol}://{new_host}:{new_port}/ws/status/frontend/"
            }
        }

    except Exception as e:
        logger.error(f"更新 WebSocket 配置失败: {e}")
        return {"code": 500, "message": f"配置更新失败: {str(e)}"}
