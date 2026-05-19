# 项目分析报告

## 1. 项目结构

```
d:\local_pysys/
├── backend/          # FastAPI后端服务
├── vue-element-plus-admin-master/  # Vue 3前端框架
├── src/              # 前端自定义组件
├── .venv/            # Python虚拟环境
└── requirements.txt  # Python依赖
```

## 2. 技术栈

### 后端
- **框架**: FastAPI (Python 3.13)
- **数据库**: MySQL (PyMySQL驱动)
- **认证**: JWT (JSON Web Token)
- **密码加密**: BCrypt + 兼容MD5
- **WebSocket**: 实时进度和日志推送
- **配置管理**: INI配置文件 + 环境变量覆盖

### 前端
- **框架**: Vue 3 + TypeScript
- **UI组件库**: Element Plus
- **构建工具**: Vite 6
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **图表**: ECharts
- **国际化**: Vue I18n

## 3. 核心功能模块

### 3.1 数据同步服务
- **功能**: 从远程数据库同步数据到本地数据库
- **同步策略**: 按月份批量同步，支持断点续传
- **表命名规则**: `gbupload_etctu_as_YYYYMMDD` (基于日期)
- **同步流程**:
  1. 复制表结构
  2. 分批复制数据 (默认批次大小1000)
  3. 实时更新同步进度
  4. 支持停止/恢复同步

### 3.2 用户认证与授权
- **认证方式**: JWT令牌认证
- **权限模型**: RBAC (基于角色的访问控制)
- **核心表结构**:
  - `users`: 用户信息
  - `roles`: 角色定义
  - `menus`: 菜单权限
  - `user_roles`: 用户-角色关联
  - `role_menus`: 角色-菜单关联

### 3.3 系统管理
- **部门管理**: 支持树形结构，包含名称、排序、状态等
- **用户管理**: 支持创建、编辑、删除用户，分配角色
- **角色管理**: 支持创建角色，分配菜单权限
- **菜单管理**: 支持多级菜单，包含路径、组件、权限标识等

### 3.4 配置管理
- **配置类型**:
  - 远程数据库连接
  - 本地数据库连接
  - 用户数据库连接
  - 同步参数配置
- **配置加载顺序**: 环境变量 > 配置文件 > 默认值

### 3.5 日志系统
- **日志级别**: INFO, ERROR
- **输出方式**:
  - 控制台日志
  - 文件日志 (`app.log`, `error.log`, `sync_service.log`)
  - WebSocket实时推送

## 4. 核心API接口

### 4.1 认证相关
- `POST /api/login/`: 用户登录
- `POST /api/register/`: 用户注册
- `GET /api/user/loginOut`: 用户登出

### 4.2 配置相关
- `GET /api/config/`: 获取当前配置
- `POST /api/config/`: 保存配置
- `POST /api/config/test-remote/`: 测试远程数据库连接
- `POST /api/config/test-local/`: 测试本地数据库连接

### 4.3 同步相关
- `GET /api/sync/months/`: 获取可选月份列表
- `POST /api/start-sync/`: 开始同步
- `POST /api/stop-sync/`: 停止同步
- `GET /api/sync/status/`: 获取同步状态

### 4.4 系统管理
- `GET /api/departments/`: 获取部门列表
- `POST /api/departments/`: 创建部门
- `PUT /api/departments/{department_id}`: 更新部门
- `DELETE /api/departments/{department_id}`: 删除部门
- `GET /api/users/`: 获取用户列表
- `POST /api/users/`: 创建用户
- `PUT /api/users/{user_id}`: 更新用户
- `DELETE /api/users/{user_id}`: 删除用户
- `GET /api/roles/`: 获取角色列表
- `POST /api/roles/`: 创建角色
- `PUT /api/roles/{role_id}`: 更新角色
- `DELETE /api/roles/{role_id}`: 删除角色
- `GET /api/menus/`: 获取菜单列表
- `POST /api/menus/`: 创建菜单
- `PUT /api/menus/{menu_id}`: 更新菜单
- `DELETE /api/menus/{menu_id}`: 删除菜单

### 4.5 WebSocket接口
- `ws://localhost:8000/ws/sync-progress/`: 同步进度推送
- `ws://localhost:8000/ws/logs/`: 日志推送

## 5. 数据模型

### 5.1 部门表 (departments)
| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | int | 部门ID |
| name | varchar | 部门名称 |
| parent_id | int | 父部门ID |
| sort_order | int | 排序顺序 |
| status | int | 状态 (1: 启用, 0: 禁用) |

### 5.2 用户表 (users)
| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | int | 用户ID |
| username | varchar | 用户名 |
| password | varchar | 密码 (MD5或BCrypt) |
| nickname | varchar | 昵称 |
| email | varchar | 邮箱 |
| department_id | int | 所属部门ID |
| status | int | 状态 (1: 启用, 0: 禁用) |

### 5.3 角色表 (roles)
| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | int | 角色ID |
| name | varchar | 角色名称 |
| code | varchar | 角色编码 |
| description | text | 角色描述 |
| status | int | 状态 (1: 启用, 0: 禁用) |

### 5.4 菜单表 (menus)
| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | int | 菜单ID |
| parent_id | int | 父菜单ID |
| name | varchar | 菜单名称 |
| icon | varchar | 菜单图标 |
| path | varchar | 路由路径 |
| component | varchar | 组件路径 |
| permission | varchar | 权限标识 |
| sort_order | int | 排序顺序 |
| status | int | 状态 (1: 启用, 0: 禁用) |
| visible | int | 是否可见 (1: 可见, 0: 隐藏) |

## 6. 关键业务流程

### 6.1 用户登录流程
1. 用户提交用户名和密码
2. 系统验证用户名和密码 (兼容MD5和BCrypt)
3. 生成JWT令牌返回给前端
4. 前端存储令牌，用于后续API请求

### 6.2 数据同步流程
1. 用户选择要同步的月份
2. 系统生成该月份的所有日期
3. 对每个日期生成对应的表名
4. 检查远程数据库中表是否存在
5. 复制表结构到本地数据库
6. 分批复制数据到本地数据库
7. 实时更新同步进度
8. 同步完成后更新状态

### 6.3 权限验证流程
1. 用户请求API时携带JWT令牌
2. 系统解析令牌，获取用户名
3. 查询用户角色和权限
4. 检查用户是否具有访问该API的权限
5. 有权限则继续执行，否则返回403错误

## 7. 配置说明

### 7.1 配置文件结构 (`backend/config.ini`)
```ini
[REMOTE_DB]
; 远程数据库配置

[LOCAL_DB]
; 本地数据库配置

[USER_DB]
; 用户数据库配置

[SYNC]
; 同步参数配置
```

### 7.2 核心配置项
| 配置项 | 说明 |
|-------|------|
| sync_months | 默认同步月份 (YYYY-MM格式) |
| sync_date_range | 同步日期范围 |
| primary_keys | 主键字段名 |
| batch_size | 批量同步大小 |
| retry_count | 重试次数 |
| timeout | 连接超时时间 |

## 8. 部署说明

### 8.1 后端部署
1. 安装依赖: `pip install -r requirements.txt`
2. 运行服务: `uvicorn backend.main:app --reload`
3. 访问地址: `http://localhost:8000`

### 8.2 前端部署
1. 安装依赖: `pnpm install`
2. 开发模式: `pnpm dev`
3. 构建生产版本: `pnpm build:pro`

## 9. 监控与日志

### 9.1 日志文件位置
- 应用日志: `backend/logs/app.log`
- 错误日志: `backend/logs/error.log`
- 同步服务日志: `backend/logs/sync_service.log`

### 9.2 WebSocket监控
- 同步进度: `ws://localhost:8000/ws/sync-progress/`
- 实时日志: `ws://localhost:8000/ws/logs/`

## 10. 总结

该项目是一个基于FastAPI和Vue 3的前后端分离系统，主要功能是实现远程数据库到本地数据库的数据同步，并提供完整的RBAC权限管理系统。系统具有以下特点：

1. **模块化设计**: 后端采用FastAPI的模块化路由设计，前端基于Vue 3组件化开发
2. **实时通信**: 通过WebSocket实现同步进度和日志的实时推送
3. **高可靠性**: 同步服务支持断点续传和重试机制
4. **安全认证**: 采用JWT令牌认证和BCrypt密码加密
5. **灵活配置**: 支持环境变量和配置文件的灵活配置
6. **完整的权限管理**: 基于RBAC模型的部门、用户、角色、菜单管理
7. **良好的日志系统**: 支持多级别、多输出方式的日志管理

该系统适合需要定期从远程数据库同步数据到本地，并需要进行权限管理的企业级应用场景。