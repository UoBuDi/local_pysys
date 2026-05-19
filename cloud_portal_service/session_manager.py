import time
import threading
import logging
from typing import Dict, Optional, List, Any, Tuple
from portal_client import PortalClient
from config import config, Limits

logger = logging.getLogger(__name__)


class AutoRenewEngine:
    """自动续期引擎 - 后台线程定时调用 automaticLogin 保活会话"""

    def __init__(self, session_store: 'SessionStore'):
        self._store = session_store
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._renew_loop, daemon=True, name="AutoRenewEngine")
        self._thread.start()
        logger.info("[自动续期] 引擎已启动, 间隔=%ds", config.AUTO_RENEW_INTERVAL)

    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        logger.info("[自动续期] 引擎已停止")

    def _renew_loop(self):
        while self._running and not self._stop_event.is_set():
            try:
                interval = config.AUTO_RENEW_INTERVAL
                self._stop_event.wait(timeout=interval)

                if not self._running:
                    break

                self._renew_all_sessions()

            except Exception as e:
                logger.error("[自动续期] 循环异常: %s", e, exc_info=True)

    def _renew_all_sessions(self):
        session_ids = self._store.get_all_session_ids()
        for sid in session_ids:
            try:
                client = self._store.get(sid)
                if not client or not client.access_token:
                    continue

                result = client.automatic_login()
                if result['success']:
                    logger.info("[自动续期] 会话 %s... 续期成功", sid[:8])
                else:
                    logger.warning("[自动续期] 会话 %s... 续期失败: %s", sid[:8], result.get('error'))

                    status = client.check_login_status_by_api()
                    if not status['logged_in']:
                        logger.error(
                            "[自动续期] 会话 %s... 确认已失效，标记需重登: %s",
                            sid[:8], status.get('reason')
                        )
                        client.needs_relogin = True
                        client.relogin_reason = status.get('reason', '登录过期')

            except Exception as e:
                logger.error("[自动续期] 会话 %s... 异常: %s", sid[:8], e)


class CaptchaTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._captcha_timestamps: Dict[str, float] = {}
    
    def store(self, session_id: str, uuid: str) -> None:
        key = f"{session_id}:{uuid}"
        with self._lock:
            self._captcha_timestamps[key] = time.time()
    
    def validate(self, session_id: str, uuid: str) -> Tuple[bool, str]:
        key = f"{session_id}:{uuid}"
        with self._lock:
            timestamp = self._captcha_timestamps.pop(key, None)
            
            if timestamp is None:
                return False, "验证码不存在或已使用"
            
            elapsed = time.time() - timestamp
            if elapsed > Limits.CAPTCHA_TTL:
                return False, f"验证码已过期（有效期{Limits.CAPTCHA_TTL}秒）"
            
            return True, ""
    
    def clear_session(self, session_id: str) -> None:
        with self._lock:
            keys_to_remove = [k for k in self._captcha_timestamps.keys() if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del self._captcha_timestamps[key]


class SessionStore:
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: Dict[str, PortalClient] = {}
        self._owner_ids: Dict[str, str] = {}
    
    def create(self, session_id: str, client: PortalClient, owner_id: Optional[str] = None) -> None:
        with self._lock:
            if session_id in self._sessions:
                try:
                    self._sessions[session_id].logout()
                except Exception as e:
                    logger.error(f"登出旧会话失败: {session_id}, 错误: {e}")
            
            self._sessions[session_id] = client
            if owner_id:
                self._owner_ids[session_id] = owner_id
                client.owner_id = owner_id
    
    def get(self, session_id: str) -> Optional[PortalClient]:
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_owner(self, session_id: str) -> Optional[str]:
        with self._lock:
            return self._owner_ids.get(session_id)
    
    def validate_owner(self, session_id: str, owner_id: str) -> bool:
        with self._lock:
            stored_owner = self._owner_ids.get(session_id)
            if stored_owner is None:
                return True
            return stored_owner == owner_id
    
    def remove(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                try:
                    self._sessions[session_id].logout()
                except Exception as e:
                    logger.error(f"登出会话失败: {session_id}, 错误: {e}")
                del self._sessions[session_id]
                logger.info(f"移除会话: {session_id}")
            
            if session_id in self._owner_ids:
                del self._owner_ids[session_id]
    
    def update_timestamp(self, session_id: str) -> None:
        pass
    
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
                    'needs_relogin': status.get('needs_relogin', False),
                    'relogin_reason': status.get('relogin_reason'),
                    'owner_id': self._owner_ids.get(session_id)
                }
            return result
    
    def cleanup_expired(self) -> int:
        return 0
    
    def clear_all(self) -> int:
        with self._lock:
            count = len(self._sessions)
            for session_id in list(self._sessions.keys()):
                try:
                    self._sessions[session_id].logout()
                except Exception:
                    pass
            self._sessions.clear()
            self._owner_ids.clear()
            return count


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
        self._captcha_tracker = CaptchaTracker()
        self._auto_renew = AutoRenewEngine(self._store)
        self._last_request_time: float = time.time()
        self._idle_threshold: int = Limits.IDLE_THRESHOLD
    
    def _ensure_services_started(self) -> None:
        pass
    
    def shutdown(self) -> None:
        logger.info("[关闭] 开始关闭SessionManager...")
        self._auto_renew.stop()
        session_ids = self._store.get_all_session_ids()
        for session_id in session_ids:
            self._store.remove(session_id)
        logger.info("[关闭] SessionManager已关闭")
    
    def create_session(self, session_id: str, source_ip: Optional[str] = None, owner_id: Optional[str] = None) -> PortalClient:
        client = PortalClient(source_ip)
        self._store.create(session_id, client, owner_id)
        logger.info(f"创建新会话: {session_id}, owner: {owner_id or '未指定'}")
        return client
    
    def get_session(self, session_id: str) -> Optional[PortalClient]:
        return self._store.get(session_id)
    
    def validate_session_owner(self, session_id: str, owner_id: str) -> bool:
        return self._store.validate_owner(session_id, owner_id)
    
    def remove_session(self, session_id: str) -> None:
        self._captcha_tracker.clear_session(session_id)
        self._store.remove(session_id)
    
    def update_timestamp(self, session_id: str) -> None:
        pass

    def update_activity(self) -> None:
        self._last_request_time = time.time()

    @property
    def last_request_time(self) -> float:
        return self._last_request_time

    @property
    def idle_threshold(self) -> int:
        return self._idle_threshold

    def is_idle(self) -> bool:
        elapsed = time.time() - self._last_request_time
        return elapsed >= self._idle_threshold
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        return self._store.get_all_sessions_info()
    
    def cleanup_expired_sessions(self) -> int:
        return 0
    
    def cleanup_all_sessions(self) -> None:
        logger.info("[清理] 开始清理所有会话...")
        count = self._store.clear_all()
        logger.info(f"[清理] 已清理 {count} 个会话")

    def start_auto_renew(self) -> None:
        self._auto_renew.start()

    def stop_auto_renew(self) -> None:
        self._auto_renew.stop()
    
    def store_captcha(self, session_id: str, uuid: str) -> None:
        self._captcha_tracker.store(session_id, uuid)
    
    def validate_captcha(self, session_id: str, uuid: str) -> Tuple[bool, str]:
        return self._captcha_tracker.validate(session_id, uuid)
    
    @property
    def heartbeat_success_count(self) -> int:
        return 0
    
    @property
    def heartbeat_failure_count(self) -> int:
        return 0


def get_session_manager() -> SessionManager:
    return SessionManager()


session_manager = get_session_manager()
