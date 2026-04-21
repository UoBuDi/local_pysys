from pydantic import BaseModel, Field
from typing import Optional, List


class TokenCheckRequest(BaseModel):
    """Token 检查请求"""
    token: str = Field(..., description="JWT Token")


class TokenCheckResponse(BaseModel):
    """Token 检查结果 (内网简化版)"""
    code: int
    message: str
    data: dict = Field(default_factory=dict)


class CloudPortalLoginRequest(BaseModel):
    """云门户登录请求 (加密密码版本)"""
    portal_username: str = Field(..., description="云门户用户名")
    portal_password: str = Field(..., description="已加密的云门户密码")


class PublicKeyResponse(BaseModel):
    """RSA 公钥响应"""
    code: int
    message: str
    data: dict = Field(default_factory=dict)


class EncryptConfigResponse(BaseModel):
    """加密配置响应"""
    code: int
    message: str
    data: dict = Field(default_factory=dict)


class DepartmentCreateRequest(BaseModel):
    name: str
    parent_id: int = 0
    sort_order: int = 0
    status: int = 1


class DepartmentUpdateRequest(BaseModel):
    name: str
    parent_id: int = 0
    sort_order: int = 0
    status: int = 1


class UserCreateRequest(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    status: int = 1


class UserUpdateRequest(BaseModel):
    username: str
    password: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    status: int = 1


class RoleCreateRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    status: int = 1


class RoleUpdateRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    status: int = 1


class MenuCreateRequest(BaseModel):
    name: str
    icon: Optional[str] = None
    path: str
    component: Optional[str] = None
    parent_id: int = 0
    sort_order: int = 0
    status: int = 1
    visible: int = 1


class MenuUpdateRequest(BaseModel):
    name: str
    icon: Optional[str] = None
    path: str
    component: Optional[str] = None
    parent_id: int = 0
    sort_order: int = 0
    status: int = 1
    visible: int = 1


class AssignRoleRequest(BaseModel):
    user_id: int
    role_ids: List[int]


class AssignMenuRequest(BaseModel):
    role_id: int
    menu_ids: List[int]