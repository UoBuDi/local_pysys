from datetime import datetime
from typing import Dict, Any, Optional, List
import json

WS_PROTOCOL_VERSION = "1.0.0"

def get_timestamp() -> str:
    return datetime.now().isoformat()

def create_connected_message(client_type: str, client_id: str) -> str:
    return json.dumps({
        "type": "connected",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "client_type": client_type,
            "client_id": client_id,
            "server_time": get_timestamp()
        }
    })

def create_heartbeat_ack_message() -> str:
    return json.dumps({
        "type": "heartbeat_ack",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "server_time": get_timestamp()
        }
    })

def create_pong_message() -> str:
    return json.dumps({
        "type": "pong",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "server_time": get_timestamp()
        }
    })

def create_status_response_message(status_data: Dict[str, Any]) -> str:
    return json.dumps({
        "type": "status_response",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": status_data
    })

def create_client_joined_message(client_type: str, client_id: str, status: Dict[str, Any]) -> str:
    return json.dumps({
        "type": "client_joined",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "client_type": client_type,
            "client_id": client_id
        },
        "status": {
            "frontend_count": status.get("frontend_count", 0),
            "gui_count": status.get("gui_count", 0)
        }
    })

def create_client_left_message(client_type: str, client_id: str, status: Dict[str, Any]) -> str:
    return json.dumps({
        "type": "client_left",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "client_type": client_type,
            "client_id": client_id
        },
        "status": {
            "frontend_count": status.get("frontend_count", 0),
            "gui_count": status.get("gui_count", 0)
        }
    })

def create_status_update_message(status_data: Dict[str, Any]) -> str:
    return json.dumps({
        "type": "status_update",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": status_data
    })

def create_error_message(message: str, code: int = 400, details: Optional[str] = None) -> str:
    error_data = {
        "code": code,
        "message": message
    }
    if details:
        error_data["details"] = details
    
    return json.dumps({
        "type": "error",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": error_data
    })

def create_message_message(from_type: str, from_id: str, message_data: Dict[str, Any]) -> str:
    return json.dumps({
        "type": "message",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "from_type": from_type,
            "from_id": from_id,
            "content": message_data
        }
    })

def create_sync_progress_message(progress: int, message: str, config: Optional[Dict[str, Any]] = None) -> str:
    data = {
        "type": "config_update",
        "progress": progress,
        "message": message
    }
    if config:
        data["config"] = config
    
    return json.dumps({
        "type": "sync_progress",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": data
    })

def create_log_message(level: str, message: str) -> str:
    return json.dumps({
        "type": "log",
        "version": WS_PROTOCOL_VERSION,
        "timestamp": get_timestamp(),
        "data": {
            "level": level,
            "message": message
        }
    })
