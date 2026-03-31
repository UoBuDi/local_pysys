# 云门户查询服务

## 功能说明

云门户查询服务是一个独立的Windows GUI应用程序，用于处理前端与云门户API之间的通信。

### 主要功能

1. **验证码获取与显示**：从云门户获取验证码并返回给前端
2. **用户登录**：处理用户登录请求，管理会话Token
3. **数据查询**：转发查询请求到云门户API
4. **会话管理**：支持多用户同时使用，自动清理过期会话
5. **配置管理**：提供图形化配置界面

## 网络环境

本服务针对双网卡环境设计：

- **以太网** (172.32.48.239)：业务网络，可访问后端服务
- **以太网2** (10.143.164.29)：云门户网络，可访问云门户API

服务会自动绑定到以太网网卡提供API服务，并通过以太网2访问云门户。

## 打包为EXE可执行文件

### 打包步骤

1. 双击运行 `build.bat` 脚本
2. 脚本会自动安装PyInstaller和所有依赖
3. 打包完成后，在 `dist` 文件夹中生成 `CloudPortalService.exe`

### 打包输出

打包完成后，`dist` 文件夹包含：
- `CloudPortalService.exe` - 主程序
- `service_config.json` - 配置文件模板

### 部署到目标服务器

将 `dist` 文件夹中的所有文件复制到目标Windows服务器即可运行。

## 开发环境运行

### 方式一：使用启动脚本

双击 `run.bat` 文件，脚本会自动：
1. 创建Python虚拟环境
2. 安装所需依赖
3. 启动GUI服务

### 方式二：手动运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

## 配置说明

点击界面上的"配置"按钮可以修改以下设置：

### 网络配置
- 服务地址：GUI服务监听的IP地址（默认：172.32.48.239）
- 服务端口：GUI服务监听的端口（默认：9000）
- 以太网IP：业务网络IP
- 以太网2IP：云门户网络IP

### 门户配置
- 门户基础URL：云门户API基础地址
- SSO URL：单点登录地址
- 门户主页URL：门户主页地址
- 客户端ID：OAuth客户端ID
- 会话超时：会话过期时间（秒）

### 常规配置
- 启动时自动开始服务
- 启动时最小化到系统托盘
- 日志级别

## API接口

服务启动后提供以下API接口：

### 健康检查
```
GET /api/portal/health
```

### 获取验证码
```
GET /api/portal/captcha?session_id=xxx
```

### 登录
```
POST /api/portal/login
{
    "session_id": "xxx",
    "username": "xxx",
    "password": "xxx",
    "captcha": "xxx",
    "uuid": "xxx"
}
```

### 查询
```
POST /api/portal/query
{
    "session_id": "xxx",
    "query_params": {
        "pass_id": "xxx",
        "plate_number": "xxx",
        ...
    }
}
```

### 获取状态
```
GET /api/portal/status?session_id=xxx
```

### 登出
```
POST /api/portal/logout
{
    "session_id": "xxx"
}
```

## 系统托盘

程序支持最小化到系统托盘：
- 双击托盘图标显示主窗口
- 右键托盘图标显示菜单
- 可从托盘启动/停止服务

## 日志

运行日志保存在 `service.log` 文件中。

## 注意事项

1. 确保网络配置正确，以太网2能够访问云门户
2. 首次运行需要安装Python依赖
3. 如果端口被占用，请修改配置中的端口号
4. 会话默认1小时过期，可在配置中调整

## 故障排除

### 无法启动服务
- 检查端口是否被占用
- 检查防火墙设置
- 查看日志文件获取详细错误信息

### 无法访问云门户
- 确认以太网2网络连接正常
- 检查云门户URL配置是否正确
- 尝试在浏览器中访问云门户验证网络

### 验证码获取失败
- 检查网络连接
- 确认云门户API可访问
- 查看日志获取详细错误信息

## 文件说明

| 文件 | 说明 |
|------|------|
| main.py | GUI主程序 |
| api_server.py | Flask API服务 |
| portal_client.py | 云门户客户端 |
| session_manager.py | 会话管理器 |
| network_utils.py | 网络工具 |
| config.py | 配置管理 |
| build.spec | PyInstaller打包配置 |
| build.bat | 打包脚本 |
| run.bat | 开发环境启动脚本 |
| requirements.txt | Python依赖列表 |
