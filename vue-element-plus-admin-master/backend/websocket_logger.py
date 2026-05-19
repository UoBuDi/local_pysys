import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

ws_logger = logging.getLogger("websocket")
ws_logger.setLevel(logging.DEBUG)

ws_file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "websocket.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
ws_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
ws_logger.addHandler(ws_file_handler)

class WebSocketLogger:
    @staticmethod
    def log_connection(client_type: str, client_id: str, ip: str = "unknown"):
        ws_logger.info(f"连接: type={client_type}, id={client_id}, ip={ip}")
    
    @staticmethod
    def log_disconnection(client_type: str, client_id: str, reason: str = "normal"):
        ws_logger.info(f"断开: type={client_type}, id={client_id}, reason={reason}")
    
    @staticmethod
    def log_heartbeat(client_type: str, client_id: str):
        ws_logger.debug(f"心跳: type={client_type}, id={client_id}")
    
    @staticmethod
    def log_error(client_type: str, client_id: str, error: str):
        ws_logger.error(f"错误: type={client_type}, id={client_id}, error={error}")
    
    @staticmethod
    def log_message(client_type: str, client_id: str, message_type: str):
        ws_logger.debug(f"消息: type={client_type}, id={client_id}, msg_type={message_type}")
