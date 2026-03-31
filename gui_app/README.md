# 数据管理系统 - 桌面版

基于PyQt6构建的Windows桌面应用程序，集成FastAPI后端服务。

## 功能模块

### 系统管理
- 系统配置：配置远程和本地数据库连接
- 数据库连接测试：测试数据库连接状态

### 用户权限管理
- 用户管理：用户的增删改查
- 角色管理：角色的增删改查
- 菜单管理：菜单的树形结构管理
- 权限管理：权限的增删改查

### 数据管理
- 数据同步：启动/暂停/停止数据同步任务
- 拆分匹配：查询和导出拆分匹配数据
- 详单查询：按条件查询交易详单
- 路径匹配：查询车辆行驶路径

### 记录管理
- 特情记录：U型车、未付车、无卡车记录管理
- 排班管理：班组、班次、人员、排班记录管理

### 任务管理
- 定时任务：查看和管理定时任务
- 执行历史：查看任务执行历史记录

## 开发环境

### 系统要求
- Windows 10/11
- Python 3.10+
- MySQL 5.7+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

开发模式：
```bash
python main.py
```

或双击 `run.bat`

### 打包发布

```bash
build.bat
```

打包后的可执行文件位于 `dist` 目录。

## 目录结构

```
gui_app/
├── main.py              # 主程序入口
├── requirements.txt     # Python依赖
├── build.spec          # PyInstaller配置
├── build.bat           # 打包脚本
├── run.bat             # 运行脚本
├── modules/            # 功能模块
│   ├── config.py       # 系统配置
│   ├── database_test.py # 数据库测试
│   ├── users.py        # 用户管理
│   ├── roles.py        # 角色管理
│   ├── menus.py        # 菜单管理
│   ├── permissions.py  # 权限管理
│   ├── sync.py         # 数据同步
│   ├── split_match.py  # 拆分匹配
│   ├── detail_query.py # 详单查询
│   ├── path_match.py   # 路径匹配
│   ├── special_records.py # 特情记录
│   ├── scheduling.py   # 排班管理
│   ├── scheduled_tasks.py # 定时任务
│   └── task_history.py # 执行历史
├── utils/              # 工具类
│   └── api_client.py   # API客户端
└── resources/          # 资源文件
    └── icon.ico        # 程序图标
```

## 技术栈

- **前端框架**: PyQt6
- **后端框架**: FastAPI
- **数据库**: MySQL (PyMySQL)
- **HTTP客户端**: Requests
- **Excel处理**: OpenPyXL
- **定时任务**: APScheduler
- **打包工具**: PyInstaller

## 注意事项

1. 首次运行前请确保MySQL服务已启动
2. 需要先配置数据库连接信息
3. 后端服务会自动在8000端口启动
4. 打包前请确保所有依赖已安装
