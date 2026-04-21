from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import os

STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "ws_stats.json")

class WebSocketStats:
    def __init__(self):
        self.total_connections = 0
        self.total_disconnections = 0
        self.peak_connections = 0
        self.start_time = datetime.now()
        self.connection_log: List[Dict[str, Any]] = []
        self._load_stats()
    
    def _load_stats(self):
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.total_connections = data.get("total_connections", 0)
                    self.total_disconnections = data.get("total_disconnections", 0)
                    self.peak_connections = data.get("peak_connections", 0)
                    self.start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))
                    self.connection_log = data.get("connection_log", [])[-1000:]
        except Exception:
            pass
    
    def _save_stats(self):
        try:
            os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
            data = {
                "total_connections": self.total_connections,
                "total_disconnections": self.total_disconnections,
                "peak_connections": self.peak_connections,
                "start_time": self.start_time.isoformat(),
                "connection_log": self.connection_log[-1000:]
            }
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def record_connection(self, client_type: str, client_id: str):
        self.total_connections += 1
        current = self.get_current_connections()
        if current > self.peak_connections:
            self.peak_connections = current
        self.connection_log.append({
            "event": "connected",
            "client_type": client_type,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        self._save_stats()
    
    def record_disconnection(self, client_type: str, client_id: str):
        self.total_disconnections += 1
        self.connection_log.append({
            "event": "disconnected",
            "client_type": client_type,
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        self._save_stats()
    
    def get_current_connections(self) -> int:
        return self.total_connections - self.total_disconnections
    
    def get_uptime(self) -> str:
        delta = datetime.now() - self.start_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_connections": self.total_connections,
            "total_disconnections": self.total_disconnections,
            "current_connections": self.get_current_connections(),
            "peak_connections": self.peak_connections,
            "uptime": self.get_uptime(),
            "start_time": self.start_time.isoformat()
        }
    
    def get_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            log for log in self.connection_log
            if datetime.fromisoformat(log["timestamp"]) > cutoff_time
        ]

ws_stats = WebSocketStats()
