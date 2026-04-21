# 服务管理工具

## 功能说明

这是一个用于管理前后端服务的GUI工具，主要功能包括：

1. **服务控制**
   - 启动/停止后端服务（端口8000）
   - 启动/停止前端服务（端口4000）
   - 一键重启所有服务
   - 一键停止所有服务

2. **端口监控**
   - 实时监控端口使用状态
   - 显示占用端口的进程ID和进程名称
   - 快速结束占用端口的进程

3. **健康检查**
   - 自动检测服务健康状态
   - 显示服务运行状态（正常/异常）

4. **日志查看**
   - 实时显示后端和前端服务日志
   - 支持清空日志

5. **配置管理**
   - 支持外部配置文件
   - 退出时可选择是否停止服务

## 配置文件

配置文件 `config.json` 位于程序同目录下：

```json
{
    "backend": {
        "dir": "D:\\local_pysys\\vue-element-plus-admin-master\\backend",
        "port": 8000,
        "command": "python main.py",
        "health_check_url": "/api/health"
    },
    "frontend": {
        "dir": "D:\\local_pysys\\vue-element-plus-admin-master",
        "port": 4000,
        "command": "pnpm dev",
        "health_check_url": "/"
    },
    "monitor": {
        "interval": 3,
        "health_check_timeout": 5
    },
    "service": {
        "auto_stop_on_exit": false,
        "restart_delay": 2,
        "backend_startup_delay": 3
    }
}
```

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `backend.dir` | 后端服务目录 |
| `backend.port` | 后端服务端口 |
| `backend.command` | 后端启动命令 |
| `backend.health_check_url` | 后端健康检查路径 |
| `frontend.dir` | 前端服务目录 |
| `frontend.port` | 前端服务端口 |
| `frontend.command` | 前端启动命令 |
| `frontend.health_check_url` | 前端健康检查路径 |
| `monitor.interval` | 监控轮询间隔（秒） |
| `monitor.health_check_timeout` | 健康检查超时时间（秒） |
| `service.auto_stop_on_exit` | 退出时是否自动停止服务 |
| `service.restart_delay` | 重启服务延迟（秒） |
| `service.backend_startup_delay` | 后端启动后等待时间（秒） |

## 使用方法

### 直接运行
```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 打包成EXE
```bash
# 运行打包脚本
build.bat
```

打包后的可执行文件位于 `dist/ServiceManager.exe`

## 系统要求

- Windows 10/11
- Python 3.8+（仅开发环境需要）
- 已安装Node.js和pnpm（前端服务需要）

## 注意事项

1. 首次运行会自动创建默认配置文件
2. 可通过勾选"退出时自动停止所有服务"选项控制退出行为
3. 如果端口被其他进程占用，可以使用"结束进程"功能释放端口
4. 健康检查通过HTTP请求检测服务状态

## 版本历史

### v1.1.0
- 新增配置文件支持，替代硬编码路径
- 新增服务健康检查功能
- 新增退出时停止服务选项
- 优化日志实时读取
- 修正前端启动命令为pnpm dev
- 新增配置信息显示区域

### v1.0.0
- 初始版本
- 支持前后端服务管理
- 支持端口监控和进程管理
