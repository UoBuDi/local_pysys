import time
import threading
import logging
import atexit
import signal
import random
from typing import Dict, Optional, List, Any, Tuple
from portal_client import PortalClient
from config import config, Limits, Intervals

logger = logging.getLogger(__name__)


class SessionStats:
    def __init__(self):
        self._lock = threading.Lock()
        self._heartbeat_success: int = 0
        self._heartbeat_failure: int = 0
        self._consecutive_failures: Dict[str, int] = {}
    
    def record_success(self, session_id: str) -> None:
        with self._lock:
            self._heartbeat_success += 1
            self._consecutive_failures[session_id] = 0
    
    def record_failure(self, session_id: str) -> int:
        with self._lock:
            self._heartbeat_failure += 1
            self._consecutive_failures[session_id] = self._consecutive_failures.get(session_id, 0) + 1
            return self._consecutive_failures[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._heartbeat_success + self._heartbeat_failure
            success_rate = (self._heartbeat_success / total * 100) if total > 0 else 0
            return {
                'success': self._heartbeat_success,
                'failure': self._heartbeat_failure,
                'success_rate': success_rate,
                'consecutive_failures': dict(self._consecutive_failures)
            }
    
    def reset(self) -> None:
        with self._lock:
            self._heartbeat_success = 0
            self._heartbeat_failure = 0
            self._consecutive_failures.clear()


class RetryState:
    def __init__(self):
        self.count: int = 0
        self.next_interval: int = Limits.RETRY_INTERVAL
    
    def increment(self) -> int:
        self.count += 1
        return self.count
    
    def update_interval(self) -> None:
        self.next_interval = int(self.next_interval * Limits.RETRY_BACKOFF)
    
    def should_retry(self) -> bool:
        return self.count < Limits.MAX_RETRY_COUNT


class CaptchaTracker:
    """
    验证码追踪器 - 管理验证码的过期和验证
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._captcha_timestamps: Dict[str, float] = {}
        self._captcha_uuids: Dict[str, str] = {}
    
    def store(self, session_id: str, uuid: str) -> None:
        """
        存储验证码信息
        
        Args:
            session_id: 会话ID
            uuid: 验证码UUID
        """
        key = f"{session_id}:{uuid}"
        with self._lock:
            self._captcha_timestamps[key] = time.time()
            self._captcha_uuids[session_id] = uuid
            logger.debug(f"[验证码追踪] 存储 - session: {session_id}, uuid: {uuid}")
    
    def validate(self, session_id: str, uuid: str) -> Tuple[bool, str]:
        """
        验证验证码是否有效
        
        Args:
            session_id: 会话ID
            uuid: 验证码UUID
            
        Returns:
            (是否有效, 错误信息)
        """
        key = f"{session_id}:{uuid}"
        with self._lock:
            timestamp = self._captcha_timestamps.get(key)
            
            if timestamp is None:
                logger.warning(f"[验证码追踪] 验证码不存在 - session: {session_id}, uuid: {uuid}")
                return False, "验证码不存在或已使用"
            
            elapsed = time.time() - timestamp
            if elapsed > Limits.CAPTCHA_TTL:
                del self._captcha_timestamps[key]
                logger.warning(f"[验证码追踪] 验证码已过期 - session: {session_id}, uuid: {uuid}, 过期时间: {elapsed:.0f}秒")
                return False, f"验证码已过期（有效期{Limits.CAPTCHA_TTL}秒）"
            
            del self._captcha_timestamps[key]
            logger.info(f"[验证码追踪] 验证成功 - session: {session_id}, uuid: {uuid}")
            return True, ""
    
    def cleanup_expired(self) -> int:
        """
        清理过期的验证码记录
        
        Returns:
            清理的数量
        """
        current_time = time.time()
        expired_count = 0
        
        with self._lock:
            expired_keys = [
                key for key, timestamp in self._captcha_timestamps.items()
                if current_time - timestamp > Limits.CAPTCHA_TTL
            ]
            
            for key in expired_keys:
                del self._captcha_timestamps[key]
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"[验证码追踪] 清理了 {expired_count} 个过期验证码")
        
        return expired_count
    
    def clear_session(self, session_id: str) -> None:
        """
        清理指定会话的验证码
        """
        with self._lock:
            keys_to_remove = [k for k in self._captcha_timestamps.keys() if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del self._captcha_timestamps[key]
            
            if session_id in self._captcha_uuids:
                del self._captcha_uuids[session_id]


class RateLimiter:
    """
    频率限制器 - 控制验证码请求频率
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = {}
    
    def check_and_record(self, client_id: str) -> Tuple[bool, int]:
        """
        检查并记录请求
        
        Args:
            client_id: 客户端标识（IP或用户ID）
            
        Returns:
            (是否允许, 剩余次数)
        """
        current_time = time.time()
        
        with self._lock:
            if client_id not in self._requests:
                self._requests[client_id] = []
            
            self._requests[client_id] = [
                t for t in self._requests[client_id]
                if current_time - t < Limits.CAPTCHA_RATE_PERIOD
            ]
            
            if len(self._requests[client_id]) >= Limits.CAPTCHA_RATE_LIMIT:
                return False, 0
            
            self._requests[client_id].append(current_time)
            remaining = Limits.CAPTCHA_RATE_LIMIT - len(self._requests[client_id])
            return True, remaining
    
    def cleanup(self) -> None:
        """
        清理过期的请求记录
        """
        current_time = time.time()
        
        with self._lock:
            for client_id in list(self._requests.keys()):
                self._requests[client_id] = [
                    t for t in self._requests[client_id]
                    if current_time - t < Limits.CAPTCHA_RATE_PERIOD
                ]
                if not self._requests[client_id]:
                    del self._requests[client_id]


class SessionStore:
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: Dict[str, PortalClient] = {}
        self._timestamps: Dict[str, float] = {}
        self._retry_states: Dict[str, RetryState] = {}
        self._owner_ids: Dict[str, str] = {}
    
    def create(self, session_id: str, client: PortalClient, owner_id: Optional[str] = None) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._remove_internal(session_id)
            self._sessions[session_id] = client
            self._timestamps[session_id] = time.time()
            if owner_id:
                self._owner_ids[session_id] = owner_id
                client.owner_id = owner_id
    
    def get(self, session_id: str) -> Optional[PortalClient]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            
            elapsed = time.time() - self._timestamps.get(session_id, 0)
            if elapsed > config.SESSION_TIMEOUT:
                logger.info(f"会话已过期: {session_id}")
                self._remove_internal(session_id)
                return None
            
            return self._sessions.get(session_id)
    
    def get_owner(self, session_id: str) -> Optional[str]:
        with self._lock:
            return self._owner_ids.get(session_id)
    
    def validate_owner(self, session_id: str, owner_id: str) -> bool:
        """
        验证会话是否属于指定用户
        """
        with self._lock:
            stored_owner = self._owner_ids.get(session_id)
            if stored_owner is None:
                return True
            return stored_owner == owner_id
    
    def remove(self, session_id: str) -> None:
        with self._lock:
            self._remove_internal(session_id)
    
    def _remove_internal(self, session_id: str) -> None:
        if session_id in self._sessions:
            try:
                self._sessions[session_id].logout()
            except Exception as e:
                logger.error(f"登出会话失败: {session_id}, 错误: {e}")
            del self._sessions[session_id]
            logger.info(f"移除会话: {session_id}")
        
        if session_id in self._timestamps:
            del self._timestamps[session_id]
        
        if session_id in self._retry_states:
            del self._retry_states[session_id]
        
        if session_id in self._owner_ids:
            del self._owner_ids[session_id]
    
    def update_timestamp(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._timestamps:
                self._timestamps[session_id] = time.time()
    
    def get_all_session_ids(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())
    
    def get_all_sessions_info(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            result = {}
            for session_id, client in self._sessions.items():
                status = client.get_status()
                result[session_id] = {
                    'logged_in': status['logged_in'],
                    'user_info': status['user_info'],
                    'login_time': status['login_time'],
                    'last_activity': self._timestamps.get(session_id),
                    'needs_relogin': status.get('needs_relogin', False),
                    'relogin_reason': status.get('relogin_reason'),
                    'owner_id': self._owner_ids.get(session_id)
                }
            return result
    
    def get_retry_state(self, session_id: str) -> RetryState:
        with self._lock:
            if session_id not in self._retry_states:
                self._retry_states[session_id] = RetryState()
            return self._retry_states[session_id]
    
    def clear_retry_state(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._retry_states:
                del self._retry_states[session_id]
    
    def cleanup_expired(self) -> int:
        current_time = time.time()
        expired_count = 0
        
        with self._lock:
            expired_sessions = []
            for session_id, timestamp in self._timestamps.items():
                elapsed = current_time - timestamp
                if elapsed > config.SESSION_TIMEOUT:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self._remove_internal(session_id)
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"清理了 {expired_count} 个过期会话")
        
        return expired_count
    
    def clear_all(self) -> int:
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            self._timestamps.clear()
            self._retry_states.clear()
            self._owner_ids.clear()
            return count


class HeartbeatService:
    def __init__(self, session_store: SessionStore, stats: SessionStats):
        self._store = session_store
        self._stats = stats
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_request_time = time.time()
    
    def update_activity(self) -> None:
        self._last_request_time = time.time()
    
    def is_idle(self) -> bool:
        return time.time() - self._last_request_time > Limits.IDLE_THRESHOLD
    
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        logger.info("[心跳服务] 已启动")
    
    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            if not self._thread.join(timeout=2):
                logger.warning("[心跳服务] 线程未在2秒内结束")
    
    def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                if self.is_idle():
                    session_ids = self._store.get_all_session_ids()
                    for session_id in session_ids:
                        client = self._store.get(session_id)
                        if client and client.access_token:
                            self._send_heartbeat_with_retry(session_id, client)
                
                delay = random.randint(Intervals.HEARTBEAT_MIN, Intervals.HEARTBEAT_MAX)
                for _ in range(delay):
                    if not self._running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"[心跳循环] 异常 - 错误: {e}")
                time.sleep(60)
    
    def _send_heartbeat_with_retry(self, session_id: str, client: PortalClient) -> None:
        result = client.keep_alive()
        
        if result['success']:
            self._stats.record_success(session_id)
            self._store.clear_retry_state(session_id)
            return
        
        retry_state = self._store.get_retry_state(session_id)
        
        while retry_state.should_retry() and self._running:
            retry_state.increment()
            wait_time = retry_state.next_interval
            
            logger.info(f"[重试] 会话 {session_id} 第 {retry_state.count} 次重试，等待 {wait_time}秒")
            
            for _ in range(wait_time):
                if not self._running:
                    break
                time.sleep(1)
            
            if not self._running:
                break
            
            retry_state.update_interval()
            
            result = client.keep_alive()
            if result['success']:
                logger.info(f"[重试成功] 会话 {session_id} 第 {retry_state.count} 次重试成功")
                self._stats.record_success(session_id)
                self._store.clear_retry_state(session_id)
                return
        
        consecutive = self._stats.record_failure(session_id)
        logger.warning(f"[心跳失败] 会话 {session_id}, 连续失败: {consecutive}")
        
        if consecutive >= Limits.ALERT_THRESHOLD:
            logger.error(f"[告警] 会话 {session_id} 心跳连续失败 {consecutive} 次")
            client.needs_relogin = True
            client.relogin_reason = f"心跳连续失败 {consecutive} 次"


class SessionManager:
    _instance: Optional['SessionManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'SessionManager':
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
        self._store = SessionStore()
        self._stats = SessionStats()
        self._heartbeat = HeartbeatService(self._store, self._stats)
        self._captcha_tracker = CaptchaTracker()
        self._rate_limiter = RateLimiter()
        self._services_started = False
    
    def _ensure_services_started(self) -> None:
        if self._services_started:
            return
        
        self._services_started = True
        self._start_cleanup_thread()
        self._heartbeat.start()
        self._register_shutdown_handlers()
    
    def _register_shutdown_handlers(self) -> None:
        atexit.register(self.shutdown)
        if threading.current_thread() is threading.main_thread():
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
            except ValueError:
                pass
    
    def _signal_handler(self, signum, frame) -> None:
        logger.info(f"[关闭] 收到信号 {signum}，准备关闭...")
        self.shutdown()
    
    def shutdown(self) -> None:
        logger.info("[关闭] 开始关闭SessionManager...")
        self._heartbeat.stop()
        
        session_ids = self._store.get_all_session_ids()
        for session_id in session_ids:
            self._store.remove(session_id)
        
        self._stats.reset()
        logger.info("[关闭] SessionManager已关闭")
    
    def create_session(self, session_id: str, source_ip: Optional[str] = None, owner_id: Optional[str] = None) -> PortalClient:
        self._ensure_services_started()
        client = PortalClient(source_ip)
        self._store.create(session_id, client, owner_id)
        logger.info(f"创建新会话: {session_id}, owner: {owner_id or '未指定'}")
        return client
    
    def get_session(self, session_id: str) -> Optional[PortalClient]:
        return self._store.get(session_id)
    
    def validate_session_owner(self, session_id: str, owner_id: str) -> bool:
        """
        验证会话是否属于指定用户
        """
        return self._store.validate_owner(session_id, owner_id)
    
    def remove_session(self, session_id: str) -> None:
        self._captcha_tracker.clear_session(session_id)
        self._store.remove(session_id)
    
    def update_timestamp(self, session_id: str) -> None:
        self._store.update_timestamp(session_id)
    
    def update_activity(self) -> None:
        self._heartbeat.update_activity()
    
    def is_idle(self) -> bool:
        return self._heartbeat.is_idle()
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        return self._store.get_all_sessions_info()
    
    def cleanup_expired_sessions(self) -> int:
        return self._store.cleanup_expired()
    
    def _start_cleanup_thread(self) -> None:
        def cleanup_loop():
            while True:
                time.sleep(Intervals.CLEANUP)
                self._store.cleanup_expired()
                self._captcha_tracker.cleanup_expired()
                self._rate_limiter.cleanup()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info("会话清理线程已启动")
    
    def cleanup_all_sessions(self) -> None:
        logger.info("[清理] 开始清理所有会话...")
        count = self._store.clear_all()
        self._stats.reset()
        logger.info(f"[清理] 已清理 {count} 个会话，所有状态已重置")
    
    def store_captcha(self, session_id: str, uuid: str) -> None:
        """
        存储验证码信息
        """
        self._captcha_tracker.store(session_id, uuid)
    
    def validate_captcha(self, session_id: str, uuid: str) -> Tuple[bool, str]:
        """
        验证验证码是否有效
        """
        return self._captcha_tracker.validate(session_id, uuid)
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, int]:
        """
        检查请求频率限制
        
        Returns:
            (是否允许, 剩余次数)
        """
        return self._rate_limiter.check_and_record(client_id)
    
    @property
    def heartbeat_success_count(self) -> int:
        return self._stats.get_stats()['success']
    
    @property
    def heartbeat_failure_count(self) -> int:
        return self._stats.get_stats()['failure']
    
    @property
    def last_request_time(self) -> float:
        return self._heartbeat._last_request_time
    
    @property
    def idle_threshold(self) -> int:
        return Limits.IDLE_THRESHOLD


session_manager = SessionManager()
