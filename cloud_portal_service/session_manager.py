import time
import threading
import logging
from typing import Dict, Optional
from portal_client import PortalClient
from config import config

logger = logging.getLogger(__name__)

class SessionManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.sessions: Dict[str, PortalClient] = {}
        self.session_timestamps: Dict[str, float] = {}
        self.session_lock = threading.Lock()
        
        self._start_cleanup_thread()
    
    def create_session(self, session_id: str, source_ip: Optional[str] = None) -> PortalClient:
        with self.session_lock:
            if session_id in self.sessions:
                self.remove_session(session_id)
            
            client = PortalClient(source_ip)
            self.sessions[session_id] = client
            self.session_timestamps[session_id] = time.time()
            
            logger.info(f"创建新会话: {session_id}")
            return client
    
    def get_session(self, session_id: str) -> Optional[PortalClient]:
        with self.session_lock:
            if session_id not in self.sessions:
                return None
            
            elapsed = time.time() - self.session_timestamps.get(session_id, 0)
            if elapsed > config.SESSION_TIMEOUT:
                logger.info(f"会话已过期: {session_id}")
                self.remove_session(session_id)
                return None
            
            return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> None:
        with self.session_lock:
            if session_id in self.sessions:
                self.sessions[session_id].logout()
                del self.sessions[session_id]
                logger.info(f"移除会话: {session_id}")
            
            if session_id in self.session_timestamps:
                del self.session_timestamps[session_id]
    
    def update_timestamp(self, session_id: str) -> None:
        with self.session_lock:
            if session_id in self.session_timestamps:
                self.session_timestamps[session_id] = time.time()
    
    def get_all_sessions(self) -> Dict[str, Dict]:
        with self.session_lock:
            result = {}
            for session_id, client in self.sessions.items():
                status = client.get_status()
                result[session_id] = {
                    'logged_in': status['logged_in'],
                    'user_info': status['user_info'],
                    'login_time': status['login_time'],
                    'last_activity': self.session_timestamps.get(session_id)
                }
            return result
    
    def cleanup_expired_sessions(self) -> int:
        current_time = time.time()
        expired_count = 0
        
        with self.session_lock:
            expired_sessions = []
            for session_id, timestamp in self.session_timestamps.items():
                elapsed = current_time - timestamp
                if elapsed > config.SESSION_TIMEOUT:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.remove_session(session_id)
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"清理了 {expired_count} 个过期会话")
        
        return expired_count
    
    def _start_cleanup_thread(self) -> None:
        def cleanup_loop():
            while True:
                time.sleep(300)
                self.cleanup_expired_sessions()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info("会话清理线程已启动")

session_manager = SessionManager()
