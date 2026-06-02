# PySys 项目 Code Wiki

> 版本：2.20.0 | 最后更新：2026-06-02

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 技术栈总览](#2-技术栈总览)
- [3. 项目目录结构](#3-项目目录结构)
- [4. 整体架构设计](#4-整体架构设计)
- [5. 后端架构详解](#5-后端架构详解)
  - [5.1 入口与启动流程](#51-入口与启动流程)
  - [5.2 核心模块 (core/)](#52-核心模块-core)
  - [5.3 路由模块 (routers/)](#53-路由模块-routers)
  - [5.4 业务服务层](#54-业务服务层)
  - [5.5 数据模型定义](#55-数据模型定义)
  - [5.6 数据库层](#56-数据库层)
  - [5.7 配置管理](#57-配置管理)
  - [5.8 WebSocket 实时通信](#58-websocket-实时通信)
- [6. 前端架构详解](#6-前端架构详解)
  - [6.1 入口与初始化](#61-入口与初始化)
  - [6.2 路由系统](#62-路由系统)
  - [6.3 状态管理](#63-状态管理)
  - [6.4 HTTP 客户端](#64-http-客户端)
  - [6.5 API 接口层](#65-api-接口层)
  - [6.6 组件体系](#66-组件体系)
  - [6.7 布局系统](#67-布局系统)
  - [6.8 权限控制](#68-权限控制)
  - [6.9 国际化](#69-国际化)
- [7. 数据库设计](#7-数据库设计)
- [8. 依赖关系图](#8-依赖关系图)
- [9. 项目运行方式](#9-项目运行方式)
- [10. 部署与打包](#10-部署与打包)

---

## 1. 项目概述

PySys 是一套基于 **Vue 3 + Element Plus + FastAPI** 的前后端分离后台管理系统，面向高速公路通行数据管理场景，提供数据同步、拆分匹配、详单查询、AI稽核、云门户对接等核心业务功能，同时包含完整的 RBAC 权限管理体系。

### 核心能力

| 能力域 | 说明 |
|--------|------|
| 权限管理 | 用户/角色/菜单/部门/权限点 五级 RBAC 体系 |
| 数据同步 | 远程数据库到本地数据库的批量同步，支持暂停/恢复/重试 |
| 拆分匹配 | 通行数据拆分匹配处理，支持图片审核与导出 |
| 详单查询 | 多维度通行详单检索，支持分页与条件筛选 |
| 云门户 | 对接外部云门户系统，支持 SSO 登录、验证码 OCR、会话管理 |
| AI 稽核 | 基于云门户的 AI 审计，门架图片查询与选择 |
| 数据分析 | Dashboard 统计、车型/介质/省份分布分析 |
| 排班管理 | 班组/班次/人员/排班记录管理 |
| 实时通信 | WebSocket 双通道（前端 + GUI），支持日志推送与状态同步 |

---

## 2. 技术栈总览

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5.13 | 前端框架 |
| Element Plus | 2.13.2 | UI 组件库 |
| TypeScript | 5.7.3 | 类型系统 |
| Vite | 6.0.7 | 构建工具 |
| Pinia | 2.3.0 | 状态管理 |
| Vue Router | 4.5.0 | 路由管理 |
| Vue I18n | 11.0.1 | 国际化 |
| Axios | 1.7.9 | HTTP 客户端 |
| ECharts | 5.6.0 | 图表可视化 |
| UnoCSS | 0.65.4 | 原子化 CSS |
| Monaco Editor | 0.52.2 | 代码编辑器 |
| WangEditor | 5.1.23 | 富文本编辑器 |
| pnpm | 9.15.3 | 包管理器 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.100.0 | Web 框架 |
| Uvicorn | 0.23.0 | ASGI 服务器 |
| PyMySQL | 1.1.2 | MySQL 驱动 |
| DBUtils | 3.1.2 | 数据库连接池 |
| PyJWT | 2.8.0 | JWT 令牌 |
| Pydantic | ≥2.13.4 | 数据校验模型 |
| openpyxl | 3.1.2 | Excel 处理 |
| ddddocr | 1.6.1 | 验证码 OCR |
| schedule | ≥1.2.0 | 定时任务调度 |
| requests | ≥2.32.1 | HTTP 请求 |
| psutil | ≥5.9.0 | 系统监控 |

### 数据库

| 技术 | 用途 |
|------|------|
| MySQL | 统一数据存储（禁止使用 SQLite） |

---

## 3. 项目目录结构

```
vue-element-plus-admin-master/
├── backend/                          # 后端 Python 项目
│   ├── core/                         # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py                 # 全局配置管理（单例模式）
│   │   ├── dependencies.py           # FastAPI 依赖注入
│   │   ├── models.py                 # Pydantic 数据模型定义
│   │   ├── security.py               # JWT/密码加密安全模块
│   │   ├── utils.py                  # 通用工具函数
│   │   └── websocket_manager.py      # WebSocket 连接管理器
│   ├── routers/                      # API 路由模块
│   │   ├── __init__.py
│   │   ├── auth.py                   # 认证路由
│   │   ├── users.py                  # 用户管理路由
│   │   ├── roles.py                  # 角色管理路由
│   │   ├── menus.py                  # 菜单管理路由
│   │   ├── departments.py            # 部门管理路由
│   │   ├── permissions.py            # 权限点管理路由
│   │   ├── assignments.py            # 关联分配路由
│   │   ├── sync.py                   # 数据同步路由
│   │   ├── config.py                 # 配置管理路由
│   │   ├── analysis.py               # 数据分析路由
│   │   ├── split_match.py            # 拆分匹配路由
│   │   ├── detail_query.py           # 详单查询路由
│   │   ├── health.py                 # 健康检查路由
│   │   ├── scheduled_tasks.py        # 定时任务路由
│   │   ├── cloud_portal.py           # 云门户路由
│   │   ├── chat.py                   # 聊天路由
│   │   └── websocket_endpoints.py    # WebSocket 端点路由
│   ├── migrations/                   # 数据库迁移脚本
│   │   ├── 001_init_migration.sql    # 初始化迁移
│   │   └── 002_permission_granularity.sql  # 权限粒度增强
│   ├── docs/                         # 后端文档
│   ├── main.py                       # 应用入口
│   ├── database.py                   # 数据库连接池管理
│   ├── models.py                     # 兼容旧版模型
│   ├── config.py                     # 兼容旧版配置加载
│   ├── config.ini                    # 后端配置文件
│   ├── schema.sql                    # 数据库 Schema
│   ├── requirements.txt              # Python 依赖
│   ├── sync_service.py               # 数据同步服务
│   ├── split_match_service.py        # 拆分匹配服务
│   ├── statistics_service.py         # 统计服务
│   ├── cloud_portal_data_service.py  # 云门户数据服务
│   ├── scheduler.py                  # 定时任务调度器
│   ├── encryption.py                 # AES 加密模块
│   ├── captcha_ocr.py                # 验证码 OCR 识别
│   ├── websocket_logger.py           # WebSocket 日志
│   ├── websocket_models.py           # WebSocket 消息模型
│   ├── websocket_stats.py            # WebSocket 统计
│   └── ...                           # 其他辅助脚本
│
├── src/                              # 前端 Vue 项目源码
│   ├── api/                          # API 接口定义
│   │   ├── login/                    # 登录接口
│   │   ├── dashboard/                # Dashboard 接口
│   │   ├── department/               # 部门接口
│   │   ├── role/                     # 角色接口
│   │   ├── menu/                     # 菜单接口
│   │   ├── user-role/                # 用户角色接口
│   │   ├── sync/                     # 同步接口
│   │   ├── split-match/              # 拆分匹配接口
│   │   ├── detail-query/             # 详单查询接口
│   │   ├── path-match/               # 路径匹配接口
│   │   ├── scheduled-tasks/          # 定时任务接口
│   │   ├── cloud-portal-data/        # 云门户接口
│   │   ├── chat/                     # 聊天接口
│   │   ├── common/                   # 公共接口
│   │   ├── request/                  # 请求示例接口
│   │   └── table/                    # 表格示例接口
│   ├── axios/                        # HTTP 客户端封装
│   │   ├── config.ts                 # 请求/响应拦截器
│   │   ├── service.ts                # Axios 实例与请求服务
│   │   ├── refreshInterceptor.ts     # Token 自动刷新拦截器
│   │   └── types/                    # TypeScript 类型定义
│   ├── components/                   # 全局公共组件
│   │   ├── Avatars/                  # 头像组件
│   │   ├── Backtop/                  # 返回顶部
│   │   ├── Breadcrumb/               # 面包屑导航
│   │   ├── Button/                   # 按钮权限组件
│   │   ├── ChatFloatingIcon/         # 聊天悬浮图标
│   │   ├── ChatWindow/               # 聊天窗口
│   │   ├── CodeEditor/               # 代码编辑器
│   │   ├── Dialog/                   # 对话框（含可调整大小）
│   │   ├── Echart/                   # ECharts 图表
│   │   ├── Editor/                   # 富文本编辑器
│   │   ├── Form/                     # 动态表单
│   │   ├── Icon/                     # 图标组件
│   │   ├── IconPicker/               # 图标选择器
│   │   ├── Infotip/                  # 信息提示
│   │   ├── InputPassword/            # 密码输入框
│   │   ├── JsonEditor/               # JSON 编辑器
│   │   ├── LazyImage/                # 懒加载图片
│   │   ├── LocaleDropdown/           # 语言切换
│   │   ├── Logo/                     # Logo 组件
│   │   ├── Menu/                     # 菜单组件
│   │   └── ...                       # 其他组件
│   ├── hooks/                        # 组合式函数
│   │   ├── web/                      # Web 相关 Hooks
│   │   │   ├── useTable.ts           # 表格逻辑封装
│   │   │   ├── useForm.ts            # 表单逻辑封装
│   │   │   ├── useValidator.ts       # 表单验证
│   │   │   ├── useWatermark.ts       # 水印
│   │   │   ├── useNetwork.ts         # 网络状态
│   │   │   ├── useClipboard.ts       # 剪贴板
│   │   │   └── ...
│   │   └── component/                # 组件相关 Hooks
│   ├── layout/                       # 布局组件
│   ├── locales/                      # 国际化语言包
│   ├── router/                       # 路由配置
│   ├── store/                        # Pinia 状态管理
│   │   ├── index.ts                  # Store 入口
│   │   └── modules/                  # Store 模块
│   │       ├── user.ts               # 用户状态
│   │       ├── permission.ts         # 权限状态
│   │       ├── tagsView.ts           # 标签页视图状态
│   │       ├── locale.ts             # 语言状态
│   │       └── ...
│   ├── styles/                       # 全局样式
│   ├── utils/                        # 工具函数
│   ├── views/                        # 页面视图
│   │   ├── Dashboard/                # 仪表盘
│   │   ├── Authorization/            # 权限管理
│   │   │   ├── Department/           # 部门管理
│   │   │   ├── User/                 # 用户管理
│   │   │   ├── Menu/                 # 菜单管理
│   │   │   └── Role/                 # 角色管理
│   │   ├── SystemTools/              # 系统工具
│   │   │   ├── SyncConfig/           # 同步配置
│   │   │   ├── SyncControl/          # 同步控制
│   │   │   ├── ParamsConfig/         # 参数配置
│   │   │   ├── SplitMatch/           # 拆分匹配
│   │   │   ├── DetailQuery/          # 详单查询
│   │   │   └── PathMatch/            # 路径匹配
│   │   ├── CloudPortal/              # 云门户
│   │   ├── Scheduling/               # 排班管理
│   │   ├── PersonalCenter/           # 个人中心
│   │   └── ...
│   ├── permission.ts                 # 路由守卫
│   ├── main.ts                       # 前端入口
│   └── App.vue                       # 根组件
│
├── mock/                             # Mock 数据
├── public/                           # 静态资源
├── pro/                              # 构建产物
├── scripts/                          # 构建脚本
├── package.json                      # 前端依赖配置
├── vite.config.ts                    # Vite 构建配置
├── tsconfig.json                     # TypeScript 配置
├── Dockerfile.dev                    # Docker 开发配置
├── docker-compose.dev.yaml           # Docker Compose 配置
└── CHANGELOG.md                      # 更新日志
```

---

## 4. 整体架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (Vue 3 SPA)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │  Views   │ │ Components│ │  Store   │ │   Router   │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘ │
│       └─────────────┼───────────┼──────────────┘        │
│                ┌────┴─────┐                              │
│                │  API 层  │                              │
│                └────┬─────┘                              │
│                ┌────┴─────┐                              │
│                │  Axios   │  ← Token 自动刷新/请求缓存   │
│                └────┬─────┘                              │
└─────────────────────┼───────────────────────────────────┘
                      │ HTTP / WebSocket
┌─────────────────────┼───────────────────────────────────┐
│                ┌────┴─────┐                              │
│                │ FastAPI   │  ← CORS / GZip 中间件       │
│                └────┬─────┘                              │
│       ┌─────────────┼──────────────┐                    │
│  ┌────┴────┐  ┌─────┴─────┐  ┌─────┴──────┐           │
│  │ Routers │  │   Core    │  │  Services   │           │
│  │ (17模块) │  │ (安全/配置)│  │ (业务逻辑)  │           │
│  └────┬────┘  └─────┬─────┘  └─────┬──────┘           │
│       └─────────────┼──────────────┘                    │
│                ┌────┴─────┐                              │
│                │ Database │  ← 连接池 / 事务管理         │
│                └────┬─────┘                              │
└─────────────────────┼───────────────────────────────────┘
                      │
              ┌───────┴───────┐
              │    MySQL      │
              │ (多库: USER_DB│
              │  LOCAL_DB ... │
              └───────────────┘
```

### 请求处理流程

```
用户操作 → Vue 组件 → Pinia Action → API 函数 → Axios 请求
    → [Token 注入] → FastAPI 路由 → 依赖注入(认证/权限)
    → 业务逻辑 → SQL 执行 → MySQL → 响应返回
    → Axios 响应拦截 → Store 更新 → 视图渲染
```

---

## 5. 后端架构详解

### 5.1 入口与启动流程

**文件**: [main.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/main.py)

启动流程：

1. **创建 FastAPI 实例** — `app = FastAPI()`
2. **添加中间件** — CORS（允许全部来源）+ GZip 压缩（≥1000 字节）
3. **注册 17 个路由模块** — 通过 `app.include_router()` 注册
4. **挂载静态文件** — `/static` 路径
5. **启动事件** (`startup_event`)：
   - 初始化数据库连接池（从 `config.ini` 读取配置）
   - 启动后台统计任务线程（`statistics_service.run_statistics_task`）
   - 初始化云门户数据服务（延迟初始化）
   - 初始化路由导航日志表
6. **关闭事件** (`shutdown_event`)：
   - 关闭所有数据库连接池
   - 停止后台统计任务
   - 停止同步服务
7. **全局异常处理器**：
   - `HTTPException` → 统一 JSON 格式 `{code, message, data}`
   - `RequestValidationError` → 422 参数校验错误
   - `WebSocketDisconnect` → 400 连接断开
   - `Exception` → 500 通用错误
8. **启动服务** — `uvicorn.run(app, host="0.0.0.0", port=8001)`

### 5.2 核心模块 (core/)

#### core/config.py — 全局配置管理

**文件**: [core/config.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/core/config.py)

| 函数 | 说明 |
|------|------|
| `get_config()` | 获取全局配置对象（单例模式，懒加载） |
| `load_config_from_file()` | 从 `config.ini` 加载配置 |
| `save_config_to_file(config)` | 保存配置到 `config.ini` |
| `update_global_config(config)` | 更新全局配置对象 |

配置对象为 `configparser.ConfigParser` 实例，包含以下 Section：

| Section | 用途 |
|---------|------|
| `REMOTE_DB` | 远程数据库连接（数据源） |
| `LOCAL_DB` | 本地数据库连接 |
| `USER_DB` | 用户系统数据库 |
| `CHECK_DATA_DB` | 校验数据数据库 |
| `YIN_WU_DB` | 业务数据库 |
| `SYNC` | 同步参数配置 |
| `PATH_MATCH` | 路径匹配配置 |
| `SPLIT_MATCH` | 拆分匹配配置 |
| `DETAIL_QUERY` | 详单查询配置 |

#### core/security.py — 安全模块

**文件**: [core/security.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/core/security.py)

| 函数 | 说明 |
|------|------|
| `encrypt_password(password)` | XOR 加密密码（用于云门户密码传输） |
| `decrypt_password(encrypted)` | XOR 解密密码 |
| `hash_password(password)` | MD5 哈希密码（用于用户认证） |
| `create_access_token(data)` | 创建访问令牌（有效期 120 分钟） |
| `create_refresh_token(data)` | 创建刷新令牌（有效期 7 天） |
| `decode_token(token)` | 解码验证 JWT 令牌 |
| `get_token_expires_at()` | 获取访问令牌过期时间戳 |
| `get_refresh_token_expires_at()` | 获取刷新令牌过期时间戳 |
| `check_refresh_rate_limit(username)` | 刷新令牌频率限制（120 秒内最多 3 次） |

**JWT 配置**：
- 算法：HS256
- 访问令牌有效期：120 分钟
- 刷新令牌有效期：7 天
- 密钥：环境变量 `SECRET_KEY`，默认值 `change-me`

#### core/dependencies.py — 依赖注入

**文件**: [core/dependencies.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/core/dependencies.py)

| 依赖函数 | 说明 |
|----------|------|
| `get_db()` | 获取数据库连接（优先 USER_DB，回退 LOCAL_DB） |
| `get_current_user(credentials)` | 从 JWT 解析当前用户信息（含角色和权限） |
| `verify_token(credentials)` | 仅验证令牌有效性 |
| `require_permission(permission)` | 权限验证装饰器工厂（super_admin 角色自动放行） |

#### core/models.py — 数据模型

**文件**: [core/models.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/core/models.py)

按功能模块分组的 Pydantic 模型：

| 模块 | 模型 |
|------|------|
| 认证 | `LoginCredentials`, `RegisterCredentials`, `RefreshTokenRequest` |
| 用户管理 | `UserCreateRequest`, `UserUpdateRequest` |
| 角色管理 | `RoleCreateRequest`, `RoleUpdateRequest`, `RoleCreateWithMenuRequest`, `RoleUpdateWithMenuRequest` |
| 菜单管理 | `MenuCreateRequest`, `MenuUpdateRequest` |
| 部门管理 | `DepartmentCreateRequest`, `DepartmentUpdateRequest` |
| 权限管理 | `PermissionCreateRequest`, `PermissionUpdateRequest` |
| 关联分配 | `AssignRoleRequest`, `AssignMenuRequest`, `AssignPermissionRequest` |
| 配置管理 | `DatabaseConfig`, `SyncParamsConfig`, `FullConfigRequest`, `TestConnectionRequest`, `StartSyncRequest` |
| 拆分匹配 | `ExecuteMatchRequest`, `UpdateMatchRequest`, `SplitStatisticsRequest` |
| 详单查询 | `DetailQueryRequest` |
| 云门户 | `CloudPortalLoginRequest`, `CloudPortalQueryRequest`, `CloudPortalLogoutRequest`, `AutoLoginRequest`, `CloudPortalAccountCreate/Update`, `CloudPortalSessionUpdate`, `CloudPortalDataSyncRequest` |
| AI 审计 | `AIAuditBatchQueryRequest`, `AIAuditQueryRequest`, `AIAuditGantryImagesRequest`, `AIAuditSelectImagesRequest`, `SaveImagesRequest`, `OriginalImageRequest`, `BranchCentersRequest`, `RoadSectionsRequest`, `GantryListRequest` |
| 特情记录 | `SpecialRecordCreate`, `SpecialRecordUpdate`, `BatchDeleteRequest`, `ExportByIdsRequest` |
| 排班管理 | `SchedulingGroupCreate/Update`, `SchedulingShiftCreate/Update`, `SchedulingStaffCreate/Update`, `SchedulingRecordCreate/Update` |
| 路径匹配 | `PathMatchRequest`, `PathDetailRequest` |
| 路由日志 | `RouteNavigationLog` |

#### core/websocket_manager.py — WebSocket 连接管理

**文件**: [core/websocket_manager.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/core/websocket_manager.py)

| 类 | 说明 |
|----|------|
| `ConnectionManager` | 通用连接管理器，支持个人消息和广播 |
| `StatusConnectionManager` | 状态连接管理器，区分前端和 GUI 两种客户端 |

**StatusConnectionManager 关键方法**：

| 方法 | 说明 |
|------|------|
| `connect_frontend(ws, client_id)` | 接受前端连接 |
| `connect_gui(ws, client_id)` | 接受 GUI 连接 |
| `disconnect_frontend(ws)` | 断开前端连接 |
| `disconnect_gui(ws)` | 断开 GUI 连接 |
| `update_heartbeat(ws, client_type)` | 更新心跳时间戳 |
| `broadcast_to_frontend(msg)` | 广播消息给所有前端客户端 |
| `broadcast_to_gui(msg)` | 广播消息给所有 GUI 客户端 |
| `broadcast_all(msg)` | 广播消息给所有客户端 |
| `get_status()` | 获取当前连接状态 |

### 5.3 路由模块 (routers/)

#### 5.3.1 auth.py — 认证路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录（返回 access_token + refresh_token） |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/token/refresh` | 刷新访问令牌（含频率限制） |
| POST | `/api/token/check` | 检查令牌有效性 |
| GET | `/api/auth/public-key` | 获取 RSA 公钥 |
| GET | `/api/encrypt-config` | 获取加密配置 |

#### 5.3.2 users.py — 用户管理路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 获取用户列表（支持分页、搜索） |
| POST | `/api/users` | 创建用户 |
| PUT | `/api/users/{user_id}` | 更新用户 |
| DELETE | `/api/users/{user_id}` | 删除用户 |
| GET | `/api/users/{user_id}/menus` | 获取用户菜单 |
| GET | `/api/users/{user_id}/permissions` | 获取用户权限 |
| PUT | `/api/users/{user_id}/password` | 修改用户密码 |
| GET | `/api/user/info` | 获取当前用户信息 |

#### 5.3.3 roles.py — 角色管理路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/roles` | 获取角色列表 |
| POST | `/api/roles` | 创建角色 |
| PUT | `/api/roles/{role_id}` | 更新角色 |
| DELETE | `/api/roles/{role_id}` | 删除角色 |
| GET | `/api/roles/{role_id}/menus` | 获取角色菜单 |
| POST | `/api/roles/with-menus` | 创建角色（含菜单分配） |
| PUT | `/api/roles/{role_id}/with-menus` | 更新角色（含菜单分配） |

#### 5.3.4 menus.py — 菜单管理路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/menus` | 获取菜单列表（树形结构） |
| POST | `/api/menus` | 创建菜单 |
| PUT | `/api/menus/{menu_id}` | 更新菜单 |
| DELETE | `/api/menus/{menu_id}` | 删除菜单 |

#### 5.3.5 departments.py — 部门管理路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/departments` | 获取部门树形结构 |
| POST | `/api/departments` | 创建部门 |
| PUT | `/api/departments/{dept_id}` | 更新部门 |
| DELETE | `/api/departments/{dept_id}` | 删除部门 |

#### 5.3.6 permissions.py — 权限点管理路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/permissions` | 获取权限点列表 |
| POST | `/api/permissions` | 创建权限点 |
| PUT | `/api/permissions/{permission_id}` | 更新权限点 |
| DELETE | `/api/permissions/{permission_id}` | 删除权限点 |

#### 5.3.7 assignments.py — 关联分配路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/assignments/user-roles` | 为用户分配角色 |
| POST | `/api/assignments/role-menus` | 为角色分配菜单 |
| POST | `/api/assignments/role-permissions` | 为角色分配权限 |

所有分配操作使用事务保护。

#### 5.3.8 sync.py — 数据同步路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sync/start` | 启动同步任务 |
| POST | `/api/sync/stop` | 停止同步任务 |
| POST | `/api/sync/pause` | 暂停同步任务 |
| POST | `/api/sync/resume` | 恢复同步任务 |
| GET | `/api/sync/status` | 获取同步状态 |
| GET | `/api/sync/history` | 获取同步历史 |

#### 5.3.9 config.py — 配置管理路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config` | 获取系统配置 |
| POST | `/api/config` | 保存系统配置 |
| POST | `/api/config/test-connection` | 测试数据库连接 |
| GET | `/api/config/tables` | 获取数据库表列表 |
| GET | `/api/config/databases` | 获取可用数据库列表 |

#### 5.3.10 analysis.py — 数据分析路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/analysis/total` | 总数据量统计 |
| GET | `/api/analysis/vehicle-type` | 车型分布统计 |
| GET | `/api/analysis/medium-type` | 介质类型统计 |
| GET | `/api/analysis/province` | 省份数据统计 |

#### 5.3.11 split_match.py — 拆分匹配路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/split-match/databases` | 获取可用数据库列表 |
| GET | `/api/split-match/tables` | 获取数据表列表 |
| GET | `/api/split-match/data` | 查询拆分匹配数据 |
| GET | `/api/split-match/images/{record_id}` | 获取匹配图片 |
| POST | `/api/split-match/export` | 导出匹配数据 |
| POST | `/api/split-match/execute` | 执行匹配 |
| PUT | `/api/split-match/update` | 更新匹配数据（乐观锁） |
| GET | `/api/split-match/statistics` | 拆分统计数据 |

#### 5.3.12 detail_query.py — 详单查询路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/detail-query/search` | 通行记录查询（多条件筛选 + 分页） |

#### 5.3.13 health.py — 健康检查路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 应用健康状态检查 |
| GET | `/api/health/db` | 数据库连接状态检测 |

#### 5.3.14 scheduled_tasks.py — 定时任务路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/scheduled-tasks/execute` | 手动执行统计任务 |
| GET | `/api/scheduled-tasks/history` | 获取任务执行历史 |
| GET | `/api/scheduled-tasks/status` | 获取任务状态 |
| GET | `/api/dashboard/stats` | Dashboard 统计数据 |

#### 5.3.15 cloud_portal.py — 云门户路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cloud-portal/captcha` | 获取验证码 |
| POST | `/api/cloud-portal/login` | 云门户登录 |
| POST | `/api/cloud-portal/auto-login` | 自动登录 |
| POST | `/api/cloud-portal/logout` | 云门户登出 |
| GET | `/api/cloud-portal/session-status` | 会话状态检查 |
| PUT | `/api/cloud-portal/session` | 更新会话 ID |
| POST | `/api/cloud-portal/account` | 绑定云门户账号 |
| PUT | `/api/cloud-portal/account` | 更新云门户账号 |
| GET | `/api/cloud-portal/account` | 获取云门户账号 |
| POST | `/api/cloud-portal/data-sync` | 云门户数据同步 |
| POST | `/api/cloud-portal/ai-audit/batch-query` | AI 审计批量查询 |
| POST | `/api/cloud-portal/ai-audit/query` | AI 审计查询 |
| POST | `/api/cloud-portal/ai-audit/gantry-images` | 门架图片查询 |
| POST | `/api/cloud-portal/ai-audit/select-images` | 图片选择 |
| POST | `/api/cloud-portal/ai-audit/save-images` | 保存图片 |
| POST | `/api/cloud-portal/ai-audit/original-image` | 获取原图 |
| GET | `/api/cloud-portal/branch-centers` | 分中心列表 |
| POST | `/api/cloud-portal/road-sections` | 路段列表 |
| POST | `/api/cloud-portal/gantry-list` | 门架列表 |
| ... | 特情记录 CRUD、排班管理等 | 完整业务 CRUD |

#### 5.3.16 chat.py — 聊天路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/send` | 发送聊天消息 |

#### 5.3.17 websocket_endpoints.py — WebSocket 端点

| 端点 | 说明 |
|------|------|
| `ws://host:8001/ws/logs` | 日志推送 WebSocket |
| `ws://host:8001/ws/status/frontend` | 前端状态 WebSocket |
| `ws://host:8001/ws/status/gui` | GUI 状态 WebSocket |

### 5.4 业务服务层

#### sync_service.py — 数据同步服务

负责远程数据库到本地数据库的批量数据同步，核心功能：
- 按月份批量同步数据
- 支持暂停/恢复/停止
- 批量提交（batch_size 可配置）
- 失败重试（retry_count 可配置）
- 通过 WebSocket 推送同步进度

#### split_match_service.py — 拆分匹配服务

负责通行数据的拆分匹配业务逻辑：
- 数据查询与过滤
- 匹配算法执行
- 乐观锁并发控制
- 图片关联管理

#### statistics_service.py — 统计服务

后台统计任务执行器：
- 定时执行统计计算
- Dashboard 数据聚合
- 后台线程运行

#### cloud_portal_data_service.py — 云门户数据服务

与外部云门户系统交互的核心服务：
- 会话管理（登录/登出/会话刷新）
- 验证码 OCR 识别（ddddocr）
- AI 稽核数据查询
- 门架图片获取
- 延迟初始化策略

#### scheduler.py — 定时任务调度器

基于 `schedule` 库的任务调度：
- 定时执行统计任务
- 定时检查云门户会话

#### encryption.py — AES 加密模块

提供 AES 加密/解密功能，用于敏感数据保护。

#### captcha_ocr.py — 验证码识别

基于 `ddddocr` 的验证码 OCR 识别，用于云门户自动登录。

### 5.5 数据模型定义

项目存在两套模型定义：

| 文件 | 用途 |
|------|------|
| `core/models.py` | 新版模型，按功能模块分组，字段更完整 |
| `models.py`（根目录） | 旧版兼容模型，字段较简略 |

**建议**：新代码统一使用 `core/models.py` 中的模型。

### 5.6 数据库层

**文件**: [database.py](file:///D:/local_pysys/vue-element-plus-admin-master/backend/database.py)

#### 连接池管理

```python
db_pools: Dict[str, PooledDB] = {}
```

| 函数 | 说明 |
|------|------|
| `create_db_pool(config, sections, max_connections)` | 批量创建连接池 |
| `get_db_connection(db_key, config)` | 上下文管理器，自动获取/归还连接 |
| `transaction(conn)` | 事务上下文管理器，自动 commit/rollback |
| `close_all_pools()` | 关闭所有连接池 |
| `test_db_connection(host, port, user, password, database)` | 测试数据库连接 |
| `create_db_connection(section, config)` | 兼容旧接口（优先连接池） |
| `get_database_tables(conn)` | 获取数据库表列表 |
| `table_exists(conn, table_name)` | 检查表是否存在 |
| `get_available_databases(host, port, user, password)` | 获取可用数据库列表 |

#### 连接池配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `maxconnections` | 10 | 最大连接数 |
| `mincached` | 2 | 最小缓存连接数 |
| `maxcached` | 5 | 最大缓存连接数 |
| `blocking` | True | 连接池耗尽时阻塞等待 |
| `ping` | 1 | 每次获取连接时检查连通性 |
| `connect_timeout` | 5 | 连接超时（秒） |
| `read_timeout` | 30 | 读取超时（秒） |
| `write_timeout` | 30 | 写入超时（秒） |

### 5.7 配置管理

**配置文件**: [config.ini](file:///D:/local_pysys/vue-element-plus-admin-master/backend/config.ini)

配置加载链路：

```
config.ini → core/config.py (get_config 单例) → database.py (创建连接池)
                                              → routers/* (业务逻辑读取)
```

### 5.8 WebSocket 实时通信

WebSocket 架构：

```
前端浏览器 ←── ws:///ws/status/frontend ──→ StatusConnectionManager
GUI 客户端  ←── ws:///ws/status/gui ──────→ StatusConnectionManager
所有客户端  ←── ws:///ws/logs ────────────→ ConnectionManager
```

辅助模块：

| 模块 | 说明 |
|------|------|
| `websocket_logger.py` | WebSocket 事件日志记录 |
| `websocket_models.py` | WebSocket 消息数据模型 |
| `websocket_stats.py` | 连接统计与监控 |

---

## 6. 前端架构详解

### 6.1 入口与初始化

**文件**: [src/main.ts](file:///D:/local_pysys/vue-element-plus-admin-master/src/main.ts)

初始化顺序：

```
1. createApp(App)
2. setupStore(app)          — Pinia 状态管理
3. setupI18n(app)           — 国际化
4. setupGlobCom(app)        — 全局组件注册
5. setupElementPlus(app)    — Element Plus
6. setupRouter(app)         — 路由
7. setupPermission(app)     — 权限指令
8. app.mount('#app')        — 挂载
```

### 6.2 路由系统

**文件**: [src/router/index.ts](file:///D:/local_pysys/vue-element-plus-admin-master/src/router/index.ts)

路由分为两类：

| 类型 | 说明 | 示例 |
|------|------|------|
| 常量路由 | 无需权限，始终可访问 | `/login`, `/404`, `/403`, `/500` |
| 异步路由 | 需要权限，动态加载 | Dashboard, 系统工具, 系统管理, 云门户等 |

**路由守卫**: [src/permission.ts](file:///D:/local_pysys/vue-element-plus-admin-master/src/permission.ts)

守卫逻辑：
1. 检查是否有 Token → 无则跳转登录
2. 已登录访问 `/login` → 重定向首页
3. 已登录且未加载动态路由 → 获取用户信息 → 生成动态路由
4. 路由后置守卫：记录导航日志、设置页面标题

### 6.3 状态管理

**文件**: [src/store/](file:///D:/local_pysys/vue-element-plus-admin-master/src/store/)

使用 Pinia + `pinia-plugin-persistedstate` 持久化插件。

| Store 模块 | 说明 | 持久化 |
|-----------|------|--------|
| `user` | 用户信息、Token、权限 | ✅ localStorage |
| `permission` | 路由权限、菜单 | ✅ |
| `tagsView` | 标签页视图 | ✅ |
| `locale` | 语言设置 | ✅ |

**User Store 关键状态**：

```typescript
interface UserState {
  userInfo?: UserType
  tokenKey: string           // 'Authorization'
  token: string              // 访问令牌
  refreshToken: string       // 刷新令牌
  tokenExpiresAt: number     // 访问令牌过期时间
  refreshExpiresAt: number   // 刷新令牌过期时间
  roleRouters?: string[]     // 角色路由
  permissions?: string[]     // 权限列表
  rememberMe: boolean        // 记住登录
  loginInfo?: UserLoginType  // 登录信息
}
```

### 6.4 HTTP 客户端

**文件**: [src/axios/service.ts](file:///D:/local_pysys/vue-element-plus-admin-master/src/axios/service.ts)

Axios 封装特性：

| 特性 | 说明 |
|------|------|
| 请求缓存 | GET 请求缓存 5 分钟 |
| 请求去重 | 相同请求自动合并 |
| 自动重试 | 429 状态码指数退避重试（最多 3 次） |
| Token 刷新 | 自动检测过期并刷新 |
| 请求取消 | AbortController + 取消队列 |
| 统一错误处理 | 401 自动登出 |

**拦截器链**：

```
请求: 注入 Token → 序列化参数 → 缓存检查 → 去重检查 → 发送
响应: 业务码校验 → 401 处理 → 缓存写入 → 返回数据
```

### 6.5 API 接口层

**文件**: [src/api/](file:///D:/local_pysys/vue-element-plus-admin-master/src/api/)

| API 模块 | 对应后端路由 | 说明 |
|----------|-------------|------|
| `login/` | auth.py | 登录/登出/Token 刷新 |
| `dashboard/analysis/` | analysis.py | 数据分析 |
| `dashboard/workplace/` | scheduled_tasks.py | 工作台统计 |
| `department/` | departments.py | 部门管理 |
| `role/` | roles.py | 角色管理 |
| `menu/` | menus.py | 菜单管理 |
| `user-role/` | assignments.py | 用户角色分配 |
| `sync/` | sync.py | 数据同步 |
| `split-match/` | split_match.py | 拆分匹配 |
| `detail-query/` | detail_query.py | 详单查询 |
| `path-match/` | split_match.py | 路径匹配 |
| `scheduled-tasks/` | scheduled_tasks.py | 定时任务 |
| `cloud-portal-data/` | cloud_portal.py | 云门户 |
| `chat/` | chat.py | 聊天 |

每个 API 模块通常包含：
- `index.ts` — API 函数定义
- `types.ts` — TypeScript 类型定义

### 6.6 组件体系

**文件**: [src/components/](file:///D:/local_pysys/vue-element-plus-admin-master/src/components/)

| 组件 | 说明 |
|------|------|
| `Avatars` | 头像展示 |
| `Backtop` | 返回顶部 |
| `Breadcrumb` | 面包屑导航 |
| `Button` | 按钮权限控制 |
| `ChatFloatingIcon` | 聊天悬浮图标 |
| `ChatWindow` | 聊天窗口 |
| `CloudPortalLoginDialog` | 云门户登录对话框 |
| `CodeEditor` | 代码编辑器（Monaco Editor） |
| `Collapse` | 折叠面板 |
| `ConfigGlobal` | 全局配置组件 |
| `ContentDetailWrap` | 内容详情包装器 |
| `ContentWrap` | 内容区域包装器 |
| `ContextMenu` | 右键菜单 |
| `CountTo` | 数字动画 |
| `Descriptions` | 描述列表 |
| `Dialog` | 对话框（含可调整大小版本） |
| `Echart` | ECharts 图表（静态 + 动态） |
| `Editor` | 富文本编辑器（WangEditor） |
| `Error` | 错误页面组件 |
| `Footer` | 页脚 |
| `Form` | 动态表单（支持多种组件类型） |
| `Highlight` | 文本高亮 |
| `IAgree` | 协议确认 |
| `Icon` | 图标组件（基于 Iconify） |
| `IconPicker` | 图标选择器 |
| `ImageCropping` | 图片裁剪 |
| `ImageViewer` | 图片查看器 |
| `Infotip` | 信息提示 |
| `InputPassword` | 密码输入框（含强度检测） |
| `JsonEditor` | JSON 编辑器 |
| `LazyImage` | 懒加载图片 |
| `LocaleDropdown` | 语言切换下拉框 |
| `Logo` | Logo 组件 |
| `Menu` | 菜单组件 |
| `Qrcode` | 二维码 |
| `Search` | 搜索组件 |
| `TableImagePreview` | 表格图片预览 |
| `TableVideoPreview` | 表格视频预览 |
| `Tree` | 树形组件 |
| `TreeTable` | 树形表格 |
| `UploadAvatar` | 头像上传 |
| `Waterfall` | 瀑布流 |

### 6.7 布局系统

**文件**: [src/layout/](file:///D:/local_pysys/vue-element-plus-admin-master/src/layout/)

布局结构：

```
┌──────────────────────────────────────────────┐
│                  ToolBar (顶部)                │
├────────┬─────────────────────────────────────┤
│        │           TagsView (标签页)           │
│  Menu  ├─────────────────────────────────────┤
│ (侧栏) │                                     │
│        │           AppView (内容区)            │
│        │                                     │
│        ├─────────────────────────────────────┤
│        │           Footer (页脚)              │
└────────┴─────────────────────────────────────┘
```

### 6.8 权限控制

前端权限控制分为三个层次：

| 层次 | 机制 | 说明 |
|------|------|------|
| 路由级 | 路由守卫 + 动态路由 | 根据用户角色动态生成可访问路由 |
| 菜单级 | 后端菜单数据 | 根据角色权限返回可见菜单 |
| 按钮级 | `v-hasPermi` 指令 | 控制按钮/操作的显示隐藏 |

权限数据流：

```
登录 → 获取 Token → 获取用户信息(含 roles/permissions)
    → 生成动态路由 → 渲染菜单 → 按钮权限指令
```

### 6.9 国际化

**文件**: [src/locales/](file:///D:/local_pysys/vue-element-plus-admin-master/src/locales/)

支持语言：
- 中文（zh-CN）
- 英文（en）

使用 Vue I18n 11，通过 `@intlify/unplugin-vue-i18n` 插件实现编译时优化。

---

## 7. 数据库设计

### 7.1 核心表结构

**Schema 文件**: [schema.sql](file:///D:/local_pysys/vue-element-plus-admin-master/backend/schema.sql)

#### users — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) UNIQUE | 用户名 |
| password | VARCHAR(255) | 密码（MD5 哈希） |
| nickname | VARCHAR(50) | 昵称 |
| email | VARCHAR(100) | 邮箱 |
| department_id | INT | 部门 ID |
| status | INT DEFAULT 1 | 状态（1 启用） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### departments — 部门表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| name | VARCHAR(100) | 部门名称 |
| parent_id | INT DEFAULT 0 | 父部门 ID（树形结构） |
| sort_order | INT DEFAULT 0 | 排序 |
| status | INT DEFAULT 1 | 状态 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### roles — 角色表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| name | VARCHAR(50) | 角色名称 |
| code | VARCHAR(50) UNIQUE | 角色编码 |
| description | VARCHAR(200) | 描述 |
| status | INT DEFAULT 1 | 状态 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### menus — 菜单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| parent_id | INT DEFAULT 0 | 父菜单 ID（树形结构） |
| name | VARCHAR(50) | 菜单名称 |
| icon | VARCHAR(50) | 图标 |
| path | VARCHAR(100) | 路由路径 |
| component | VARCHAR(100) | 组件路径 |
| permission | VARCHAR(100) | 权限标识 |
| sort_order | INT DEFAULT 0 | 排序 |
| status | INT DEFAULT 1 | 状态 |
| visible | INT DEFAULT 1 | 是否可见 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### user_roles — 用户角色关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| user_id | INT FK → users.id | 用户 ID |
| role_id | INT FK → roles.id | 角色 ID |
| created_at | TIMESTAMP | 创建时间 |

#### role_menus — 角色菜单关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT AUTO_INCREMENT | 主键 |
| role_id | INT FK → roles.id | 角色 ID |
| menu_id | INT FK → menus.id | 菜单 ID |
| created_at | TIMESTAMP | 创建时间 |

### 7.2 ER 关系图

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  users   │────<│  user_roles  │>────│  roles   │
└──────────┘     └──────────────┘     └──────────┘
                                           │
                                      ┌────┴───────┐
                                      │ role_menus │
                                      └────┬───────┘
                                           │
                                      ┌────┴───────┐
                                      │   menus    │
                                      └────────────┘

┌──────────────┐
│ departments  │  (树形自关联: parent_id → id)
└──────────────┘
```

### 7.3 初始数据

- **部门**: 总公司 → 技术部、市场部
- **角色**: 超级管理员(admin)、普通用户(user)
- **菜单**: 首页、数据查询、系统工具、系统管理（含子菜单共 15 项）
- **默认管理员**: admin 用户拥有所有菜单权限

### 7.4 数据库迁移

| 迁移文件 | 说明 |
|----------|------|
| `001_init_migration.sql` | 初始化核心表结构与默认数据 |
| `002_permission_granularity.sql` | 权限粒度增强（新增权限点表等） |

---

## 8. 依赖关系图

### 后端模块依赖

```
main.py
  ├── routers/* (17 个路由模块)
  │     ├── core/dependencies.py (认证/权限注入)
  │     │     ├── core/security.py (JWT/密码)
  │     │     └── core/config.py (配置)
  │     ├── database.py (连接池)
  │     │     └── config.ini
  │     ├── core/models.py (数据模型)
  │     └── 业务服务层 (sync_service, split_match_service, etc.)
  ├── database.py (启动时初始化连接池)
  ├── statistics_service.py (后台统计线程)
  ├── cloud_portal_data_service.py (延迟初始化)
  └── init_route_logs_table.py (路由日志表)
```

### 前端模块依赖

```
main.ts
  ├── store/ (Pinia)
  │     ├── modules/user.ts ←── api/login/
  │     ├── modules/permission.ts ←── api/menu/
  │     └── modules/tagsView.ts
  ├── router/index.ts ←── store/permission
  ├── permission.ts ←── store/user, store/permission
  ├── axios/service.ts
  │     ├── axios/config.ts (拦截器)
  │     ├── axios/refreshInterceptor.ts (Token 刷新)
  │     └── utils/requestCache.ts, utils/requestDedup.ts
  ├── api/* ←── axios/service.ts
  ├── components/* (全局注册)
  └── views/* ←── api/*, store/*, components/*
```

---

## 9. 项目运行方式

### 环境要求

| 依赖 | 版本要求 |
|------|----------|
| Node.js | ≥ 18.0.0 |
| pnpm | ≥ 8.1.0 |
| Python | ≥ 3.10 |
| MySQL | ≥ 5.7 |

### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 修改配置文件 config.ini（数据库连接信息）

# 4. 初始化数据库（执行 schema.sql）

# 5. 启动后端服务（端口 8001）
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 前端启动

```bash
# 1. 安装依赖
pnpm install

# 2. 开发模式启动（端口 4000）
pnpm dev

# 3. 生产构建
pnpm build:pro

# 4. 预览构建产物
pnpm serve:pro
```

### 常用脚本

| 命令 | 说明 |
|------|------|
| `pnpm dev` | 开发模式启动 |
| `pnpm build:pro` | 生产环境构建 |
| `pnpm build:dev` | 开发环境构建 |
| `pnpm build:test` | 测试环境构建 |
| `pnpm ts:check` | TypeScript 类型检查 |
| `pnpm lint:eslint` | ESLint 检查修复 |
| `pnpm lint:format` | Prettier 格式化 |
| `pnpm lint:style` | StyleLint 检查修复 |
| `pnpm clean` | 清除 node_modules |
| `pnpm p` | Plop 代码生成器 |

### Docker 启动

```bash
# 使用 Docker Compose 启动开发环境
docker-compose -f docker-compose.dev.yaml up
```

---

## 10. 部署与打包

### 打包规范

- 后端服务运行在 **8001 端口**
- 前端服务运行在 **4000 端口**
- 打包时必须明确显示**版本号**和**文件路径**
- 打包排除：`logs/` 目录、`__pycache__/` 目录、`.pyc` 文件

### 部署包目录结构

```
deploy-package.zip
├── backend/                # 后端代码
│   ├── core/               # 核心模块
│   ├── routers/            # API 路由模块
│   ├── services/           # 业务服务层
│   ├── main.py             # 后端入口
│   ├── database.py         # 数据库连接
│   ├── config.ini          # 后端配置文件
│   └── requirements.txt    # Python 依赖
├── config/                 # 部署配置
│   ├── config.ini          # 运行时配置
│   └── vite.config.ts      # 前端构建配置
├── docs/                   # 部署文档
└── frontend/               # 前端构建产物
    ├── assets/             # 静态资源
    ├── index.html          # 前端入口
    ├── favicon.ico         # 网站图标
    └── logo.png            # 网站 Logo
```

### 更新日志

项目维护 `CHANGELOG.md` 文件记录版本更新内容。
