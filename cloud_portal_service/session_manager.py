import time
import threading
import logging
import atexit
import signal
import random
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
        
        self.running = False
        self.keep_alive_thread = None
        self.keep_alive_interval = 300
        self.heartbeat_success_count = 0
        self.heartbeat_failure_count = 0
        self.heartbeat_log_interval = 12
        self.consecutive_failures = {}
        self.alert_threshold = 3
        
        self.last_request_time = time.time()
        self.idle_threshold = 600
        self.min_keep_alive_interval = 600
        self.max_keep_alive_interval = 1200
        
        self.retry_on_failure = True
        self.max_retry_count = 3
        self.retry_interval = 30
        self.retry_backoff = 1.5
        self.retry_states: Dict[str, Dict] = {}
        
        self._start_cleanup_thread()
        self._start_keep_alive_thread()
        self._register_shutdown_handlers()
    
    def _register_shutdown_handlers(self):
        atexit.register(self.shutdown)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"[关闭] 收到信号 {signum}，准备关闭...")
        self.shutdown()
    
    def shutdown(self):
        logger.info("[关闭] 开始关闭SessionManager...")
        self.running = False
        
        if self.keep_alive_thread:
            self.keep_alive_thread.join(timeout=5)
        
        with self.session_lock:
            for session_id in list(self.sessions.keys()):
                try:
                    self.sessions[session_id].logout()
                except Exception as e:
                    logger.error(f"[关闭] 登出会话失败: {session_id}, 错误: {e}")
            
            self.sessions.clear()
            self.session_timestamps.clear()
            self.retry_states.clear()
        
        logger.info("[关闭] SessionManager已关闭")
    
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
            
            if session_id in self.retry_states:
                del self.retry_states[session_id]
    
    def update_timestamp(self, session_id: str) -> None:
        with self.session_lock:
            if session_id in self.session_timestamps:
                self.session_timestamps[session_id] = time.time()
    
    def update_activity(self) -> None:
        self.last_request_time = time.time()
    
    def is_idle(self) -> bool:
        return time.time() - self.last_request_time > self.idle_threshold
    
    def get_all_sessions(self) -> Dict[str, Dict]:
        with self.session_lock:
            result = {}
            for session_id, client in self.sessions.items():
                status = client.get_status()
                result[session_id] = {
                    'logged_in': status['logged_in'],
                    'user_info': status['user_info'],
                    'login_time': status['login_time'],
                    'last_activity': self.session_timestamps.get(session_id),
                    'needs_relogin': status.get('needs_relogin', False),
                    'relogin_reason': status.get('relogin_reason')
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
    
    def _start_keep_alive_thread(self) -> None:
        if self.keep_alive_thread and self.keep_alive_thread.is_alive():
            return
        
        self.running = True
        self.keep_alive_thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.keep_alive_thread.start()
        logger.info("[心跳服务] 已启动")
    
    def _keep_alive_with_retry(self, session_id: str, client: PortalClient) -> Dict:
        result = client.keep_alive()
        
        if result['success']:
            self.retry_states.pop(session_id, None)
            self.consecutive_failures[session_id] = 0
            return result
        
        if not self.retry_on_failure:
            return result
        
        retry_state = self.retry_states.get(session_id, {
            'count': 0,
            'next_interval': self.retry_interval
        })
        
        while retry_state['count'] < self.max_retry_count and self.running:
            retry_state['count'] += 1
            wait_time = retry_state['next_interval']
            
            logger.info(f"[重试] 会话 {session_id} 第 {retry_state['count']} 次重试，等待 {wait_time}秒")
            
            for _ in range(wait_time):
                if not self.running:
                    break
                time.sleep(1)
            
            if not self.running:
                break
            
            retry_state['next_interval'] = int(wait_time * self.retry_backoff)
            
            result = client.keep_alive()
            if result['success']:
                logger.info(f"[重试成功] 会话 {session_id} 第 {retry_state['count']} 次重试成功")
                self.retry_states.pop(session_id, None)
                self.consecutive_failures[session_id] = 0
                return result
        
        logger.error(f"[重试失败] 会话 {session_id} 重试 {retry_state['count']} 次后仍然失败")
        self.retry_states[session_id] = retry_state
        return result
    
    def _keep_alive_loop(self):
        while self.running:
            try:
                if self.is_idle() and self.sessions:
                    for session_id, client in list(self.sessions.items()):
                        if client.access_token:
                            logger.debug(f"[心跳] 发送心跳 - session_id: {session_id}")
                            
                            if self.retry_on_failure:
                                result = self._keep_alive_with_retry(session_id, client)
                            else:
                                result = client.keep_alive()
                            
                            if result['success']:
                                self.heartbeat_success_count += 1
                                self.consecutive_failures[session_id] = 0
                            else:
                                self.heartbeat_failure_count += 1
                                self.consecutive_failures[session_id] = self.consecutive_failures.get(session_id, 0) + 1
                                logger.warning(f"[心跳] 失败 - session_id: {session_id}, 错误: {result.get('error')}")
                                
                                if self.consecutive_failures[session_id] >= self.alert_threshold:
                                    logger.error(f"[告警] 会话 {session_id} 心跳连续失败 {self.consecutive_failures[session_id]} 次")
                                    client.needs_relogin = True
                                    client.relogin_reason = f"心跳连续失败 {self.consecutive_failures[session_id]} 次"
                            
                            total = self.heartbeat_success_count + self.heartbeat_failure_count
                            if total > 0 and total % self.heartbeat_log_interval == 0:
                                logger.info(
                                    f"[心跳统计] 成功: {self.heartbeat_success_count}, "
                                    f"失败: {self.heartbeat_failure_count}, "
                                    f"成功率: {self.heartbeat_success_count/total*100:.1f}%"
                                )
                
                delay = random.randint(self.min_keep_alive_interval, self.max_keep_alive_interval)
                for _ in range(delay):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"[心跳循环] 异常 - 错误: {e}")
                time.sleep(60)
    
    def cleanup_all_sessions(self) -> None:
        logger.info("[清理] 开始清理所有会话...")
        
        with self.session_lock:
            session_count = len(self.sessions)
            clients_to_logout = []
            
            for session_id in list(self.sessions.keys()):
                try:
                    client = self.sessions[session_id]
                    if client:
                        clients_to_logout.append((session_id, client))
                except Exception as e:
                    logger.error(f"[清理] 获取会话失败: {session_id}, 错误: {e}")
            
            self.sessions.clear()
            self.session_timestamps.clear()
            self.consecutive_failures.clear()
            self.retry_states.clear()
            self.heartbeat_success_count = 0
            self.heartbeat_failure_count = 0
            
            logger.info(f"[清理] 已清理 {session_count} 个会话，所有状态已重置")
        
        def async_logout():
            for session_id, client in clients_to_logout:
                try:
                    client.logout()
                    logger.info(f"[清理] 会话已登出: {session_id}")
                except Exception as e:
                    logger.error(f"[清理] 登出会话失败: {session_id}, 错误: {e}")
        
        if clients_to_logout:
            import threading
            logout_thread = threading.Thread(target=async_logout, daemon=True)
            logout_thread.start()

session_manager = SessionManager()
