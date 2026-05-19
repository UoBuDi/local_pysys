# 部署文档

## 项目概述

本项目是一个数据库同步工具，包含前端管理和后端服务两部分。前端基于 vue-element-plus-admin 框架构建，后端使用 FastAPI 提供 RESTful API 服务。

## 系统要求

### 后端服务要求
- Python 3.8 或更高版本
- MySQL 5.7 或更高版本
- pip 包管理器

### 前端要求
- Node.js 16 或更高版本
- pnpm 包管理器

## 部署步骤

### 后端服务部署

1. 创建虚拟环境并激活：
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. 安装依赖：
   ```bash
   pip install -r backend/requirements.txt
   ```

3. 配置数据库连接：
   编辑 `backend/config.ini` 文件（如果没有则会自动生成），配置远程和本地数据库连接信息：
   ```ini
   [REMOTE_DB]
   host = 192.168.1.100
   port = 3306
   user = read_only
   password = your_password
   database = branchdb
   charset = utf8mb4

   [LOCAL_DB]
   host = 127.0.0.1
   port = 3306
   user = root
   password = your_password
   database = branchdb
   charset = utf8mb3

   [SYNC]
   batch_size = 1000
   retry_count = 3
   timeout = 30
   primary_keys = dataId
   ```

4. 启动后端服务：
   ```bash
   cd backend
   python main.py
   ```
   
   默认情况下，服务将在 `http://localhost:8000` 上运行。

### 前端部署

1. 安装依赖：
   ```bash
   cd vue-element-plus-admin-master
   pnpm install
   ```

2. 构建生产版本：
   ```bash
   pnpm build:pro
   ```

3. 部署前端：
   构建完成后，将 `dist` 目录中的内容部署到 Web 服务器（如 Nginx、Apache 等）。

### 开发模式运行

如果您想在开发模式下运行项目：

#### 后端开发模式
```bash
cd backend
python main.py
```

#### 前端开发模式
```bash
cd vue-element-plus-admin-master
pnpm dev
```

默认前端开发服务器运行在 `http://localhost:3000`。

## 配置说明

### 数据库配置
- `REMOTE_DB`: 远程数据库配置，通常是只读权限
- `LOCAL_DB`: 本地数据库配置，需要写入权限
- `SYNC`: 同步参数配置

### 同步参数说明
- `batch_size`: 每次同步的数据批次大小，默认1000条
- `retry_count`: 同步失败时重试次数，默认3次
- `timeout`: 数据库连接超时时间，默认30秒
- `primary_keys`: 表的主键字段，用于冲突检测

## API 接口

后端提供以下主要 API 接口：

- `GET /api/config/` - 获取当前配置
- `POST /api/config/` - 保存配置
- `POST /api/config/test-remote/` - 测试远程数据库连接
- `POST /api/config/test-local/` - 测试本地数据库连接
- `GET /api/database/tables/remote/` - 获取远程数据库表列表
- `GET /api/database/tables/local/` - 获取本地数据库表列表
- `GET /api/sync/months/` - 获取可选同步月份列表
- `POST /api/sync/start/` - 开始同步
- `POST /api/sync/stop/` - 停止同步
- `GET /api/sync/status/` - 获取同步状态

## WebSocket 接口

- `ws://localhost:8000/ws/sync-progress/` - 同步进度推送
- `ws://localhost:8000/ws/logs/` - 日志推送

## 故障排除

### 数据库连接问题
1. 检查数据库服务器是否正在运行
2. 验证网络连接是否可达数据库服务器
3. 确认数据库用户名和密码是否正确
4. 检查防火墙是否阻止了数据库端口(默认3306)
5. 确认数据库是否允许来自当前IP的连接

### 前端页面无法访问
1. 确认后端服务是否正常运行
2. 检查前端配置中的 API 地址是否正确
3. 查看浏览器控制台是否有错误信息

## 安全建议

1. 不要在配置文件中使用明文密码，建议使用环境变量
2. 限制数据库用户的权限，仅授予必要的权限
3. 在生产环境中使用 HTTPS
4. 定期更新依赖包以修复安全漏洞