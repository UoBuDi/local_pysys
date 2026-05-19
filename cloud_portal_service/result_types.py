from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional, Dict, Any

T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, data: T = None, **extra) -> 'Result[T]':
        return cls(success=True, data=data, extra=extra)
    
    @classmethod
    def fail(cls, error: str, **extra) -> 'Result[T]':
        return cls(success=False, error=error, extra=extra)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'success': self.success}
        if self.data is not None:
            result['data'] = self.data
        if self.error:
            result['error'] = self.error
        if self.extra:
            result.update(self.extra)
        return result
    
    def is_ok(self) -> bool:
        return self.success
    
    def is_fail(self) -> bool:
        return not self.success


@dataclass
class CaptchaResult:
    success: bool
    img: Optional[str] = None
    uuid: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, img: str, uuid: str) -> 'CaptchaResult':
        return cls(success=True, img=img, uuid=uuid)
    
    @classmethod
    def fail(cls, error: str) -> 'CaptchaResult':
        return cls(success=False, error=error)


@dataclass
class LoginResult:
    success: bool
    user_info: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    redirect_uri: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, user_info: Dict, access_token: str, refresh_token: str, redirect_uri: str = '') -> 'LoginResult':
        return cls(
            success=True,
            user_info=user_info,
            access_token=access_token,
            refresh_token=refresh_token,
            redirect_uri=redirect_uri
        )
    
    @classmethod
    def fail(cls, error: str) -> 'LoginResult':
        return cls(success=False, error=error)


@dataclass
class QueryResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: Any) -> 'QueryResult':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'QueryResult':
        return cls(success=False, error=error)


@dataclass
class HeartbeatResult:
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, message: str = '连接保持成功') -> 'HeartbeatResult':
        return cls(success=True, message=message)
    
    @classmethod
    def fail(cls, error: str) -> 'HeartbeatResult':
        return cls(success=False, error=error)


@dataclass
class TokenRefreshResult:
    success: bool
    error: Optional[str] = None
    
    @classmethod
    def ok(cls) -> 'TokenRefreshResult':
        return cls(success=True)
    
    @classmethod
    def fail(cls, error: str) -> 'TokenRefreshResult':
        return cls(success=False, error=error)
