1. 项目使用的框架版本及依赖
2. 测试框架的详细要求
3. 项目扩展或库需下载安装到本地，确保项目能够离线运行
4. 项目代码必须符合项目的代码规范与质量标准
5. 项目为离线应用，不依赖于网络连接，所有功能均在本地运行
6. 项目在运行时，需要确保所有依赖的库和扩展已下载安装到本地，避免依赖网络资源
7. 确保项目后端服务运行在8001端口，前端服务运行在4000端口
8. 项目代码修改过程中，如果你有疑问，可以跟我确认
9. 项目在打包时，需要明确显示打包的版本号，避免使用默认版本号
10. 项目在打包时，需要明确显示打包的文件路径，避免用户无法找到打包后的文件
11. 维护上下文，将更新日志记录在项目根目录下的CHANGELOG.md文件中，方便用户查看项目更新内容
12. 项目打包时，zip压缩包顶层直接包含 backend/、config/、docs/、frontend/ 四个目录，禁止添加额外的版本号根目录或嵌套层级。打包直接使用 D:\local_pysys\deploy 目录作为源，无需在项目目录下创建临时 pysys-v*-deploy-package 目录。zip包内部目录结构要求如下：
    ```
    backend/                # 后端代码
    ├── core/               # 核心模块（config、security、models等）
    ├── routers/            # API路由模块
    ├── services/           # 业务服务层
    ├── main.py             # 后端入口
    ├── database.py         # 数据库连接
    ├── config.ini          # 后端配置文件
    └── requirements.txt    # Python依赖
    config/                 # 部署配置
    ├── config.ini          # 运行时配置
    └── vite.config.ts      # 前端构建配置
    docs/                   # 部署文档
    frontend/               # 前端构建产物
    ├── assets/             # 静态资源（css/js/images/fonts）
    ├── index.html          # 前端入口
    ├── favicon.ico         # 网站图标
    └── logo.png            # 网站Logo
    ```
13. 项目打包时，必须排除以下文件：后端日志文件（logs/目录）、Python缓存（__pycache__/目录、.pyc文件），避免将运行时产物打包进部署包
14. 项目中禁止使用SQLite数据存储方式，全部统一使用MySQL数据库
