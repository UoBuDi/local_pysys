# 云门户查询服务

## 功能说明

云门户查询服务是一个独立的Windows GUI应用程序，用于处理前端与云门户API之间的通信。

### 主要功能

1. **验证码获取与显示**：从云门户获取验证码并返回给前端
2. **用户登录**：处理用户登录请求，管理会话Token
3. **数据查询**：转发查询请求到云门户API
4. **会话管理**：支持多用户同时使用，自动清理过期会话
5. **配置管理**：提供图形化配置界面
6. **验证码OCR识别**：本地 ddddocr 引擎自动识别验证码

## 网络环境

本服务针对双网卡环境设计：

- **以太网** (172.32.48.239)：业务网络，可访问后端服务
- **以太网2** (10.143.164.29)：云门户网络，可访问云门户API

服务会自动绑定到以太网网卡提供API服务，并通过以太网2访问云门户。

---

## 编译打包（Nuitka + zstandard）

### 编译方案概述

| 方案 | 说明 | 最终体积 |
|------|------|----------|
| PyInstaller --onefile | 传统方案，启动慢，体积大 | ~120 MB |
| Nuitka --onefile | Nuitka 原生 onefile，UPX 插件不压缩 DLL | ~95 MB |
| Nuitka --standalone + UPX | UPX 压缩 DLL，但无法生成单文件 | ~70 MB (目录) |
| **Nuitka standalone + zstandard 重打包** | **最终方案** | **~95 MB** |

### 最终方案：standalone + zstandard 重打包

**核心思路**：Nuitka 的 onefile 模式下 UPX 插件不会压缩 DLL，而 standalone 模式下 UPX 可以压缩 DLL 但无法生成单文件。因此采用两阶段编译 + 自定义重打包：

1. **standalone 编译** → 生成包含所有依赖的 main.dist 目录
2. **onefile 编译**（`--onefile-no-compression`）→ 仅获取 bootstrap exe
3. **zstandard 压缩** standalone 的 main.dist → 生成 payload
4. **附加 payload** 到 bootstrap exe 作为 RT_RCDATA 资源

### 为什么不用 UPX 压缩 DLL

经实测对比，UPX + zstandard 双重压缩适得其反：

| 方案 | main.dist | 最终 exe | zstd 压缩率 |
|------|-----------|----------|-------------|
| 纯 zstd（无 UPX） | ~130 MB | **94.80 MB** | ~73% |
| UPX + zstd | 105.85 MB | 95.02 MB | ~89.7% |

原因：UPX 压缩后的 DLL 对 zstandard 来说已经是"随机噪声"，无法再有效压缩。而原始未压缩的 DLL 包含大量重复模式（资源、对齐填充等），zstandard 可以高效压缩。纯 zstd 方案不仅体积更小，运行时还无需 UPX 解压开销，启动更快。

### 前置依赖

```
# Python 环境 (3.13)
pip install nuitka zstandard

# Nuitka 编译器缓存 (自动下载 Zig 0.15.2)
# 首次编译会自动下载，后续使用缓存

# ddddocr 模型精简
# 编译脚本自动从 site-packages/ddddocr 复制并排除不需要的模型文件
# 仅保留 common.onnx，排除 common_old.onnx 和 common_det.onnx
```

### 编译命令

```bash
cd D:\local_pysys\cloud_portal_service
python build_onefile_opt.py
```

### 编译流程详解

```
build_onefile_opt.py 执行流程:

[1/4] 准备精简的 ddddocr 模型目录
  ├── 从 site-packages/ddddocr 复制
  ├── 排除 common_old.onnx, common_det.onnx (节省 ~32 MB)
  └── 输出到 _ddddocr_slim/

[2/4] Nuitka standalone 编译
  ├── --standalone 模式
  ├── --enable-plugin=pyside6
  ├── --lto=yes (链接时优化)
  ├── 排除 cv2, scipy, QtWebEngine 等不需要的模块
  ├── --include-data-dir=_ddddocr_slim=ddddocr (嵌入精简模型)
  ├── 输出到 dist/main.dist/
  └── 备份到 _standalone_dist_backup/

[3/4] Nuitka onefile 编译 (获取 bootstrap exe)
  ├── --onefile --onefile-no-compression
  ├── 生成 bootstrap exe (仅 ~200 KB 的解压引导程序)
  └── 输出到 dist/CloudPortalService.exe

[4/4] zstandard 重打包
  ├── 用 standalone dist 替换 onefile 生成的 dist
  ├── zstandard level=22 压缩整个 dist 目录
  ├── 生成 Nuitka 兼容格式的 payload (KA + Y 头 + 文件列表 + 尾部偏移)
  ├── 通过 Windows API (UpdateResourceA) 附加为 RT_RCDATA 资源
  └── 清理临时文件
```

### Nuitka 编译参数说明

| 参数 | 说明 |
|------|------|
| `--standalone` | 生成独立目录，包含所有依赖 DLL |
| `--windows-console-mode=disable` | 隐藏控制台窗口 |
| `--enable-plugin=pyside6` | 启用 PySide6 插件支持 |
| `--lto=yes` | 链接时优化，减小体积 |
| `--nofollow-import-to=xxx` | 排除不需要的模块 |
| `--include-data-dir=_ddddocr_slim=ddddocr` | 嵌入精简的 ddddocr 模型 |
| `--onefile-tempdir-spec={CACHE_DIR}/...` | 运行时解压目录 |
| `--assume-yes-for-downloads` | 自动下载编译工具链 |

### 排除的模块及原因

| 模块 | 原因 |
|------|------|
| cv2 / opencv-python | ddddocr 不依赖 cv2，节省 ~80 MB |
| scipy | numpy 不需要 scipy，节省 ~40 MB |
| PySide6.QtWebEngine* | 无 Web 页面需求，节省 ~200 MB |
| PySide6.Qt3D* | 无 3D 渲染需求 |
| PySide6.QtPdf* | 无 PDF 需求 |
| PySide6.QtQuick* | 无 QML 需求 |
| PySide6.QtNetwork | 未使用网络模块 |
| PySide6.QtMultimedia* | 无多媒体需求 |
| unittest / pytest / setuptools | 开发工具，运行时不需要 |
| tkinter / idlelib / pydoc | 标准库开发工具 |

### 编译缓存

```
# 缓存目录 (项目本地，避免权限问题)
D:\local_pysys\cloud_portal_service\.nuitka_cache\

# 关键缓存内容:
# ├── downloads/pip/private-*/Lib/site-packages/ziglang/zig.exe  (Zig 0.15.2)
# ├── module-cache/  (Python 模块编译缓存)
# └── scons-cache/   (C 编译缓存)
```

**注意**：如果缓存中 Zig 版本为 0.16.0，可能导致链接错误（undefined symbol: frexpf）。需手动替换为 0.15.2：

```bash
# 从默认缓存复制 Zig 0.15.2
Copy-Item -Recurse -Force \
  "$env:LOCALAPPDATA\Nuitka\Nuitka\Cache\downloads\pip\*" \
  "D:\local_pysys\cloud_portal_service\.nuitka_cache\downloads\pip\"
```

### 编译产物

```
dist/
└── CloudPortalService.exe   (~95 MB, 单文件可执行)
```

运行时自动解压到 `{CACHE_DIR}/CloudPortalService/runtime/`，退出后自动清理。

### 常见编译问题

#### 1. Zig 链接错误: undefined symbol: frexpf

```
lld-link: error: <root>: undefined symbol: frexpf
```

**原因**：Nuitka 缓存中的 Zig 0.16.0 有兼容性问题。

**解决**：将缓存中的 Zig 替换为 0.15.2（见上方"编译缓存"章节）。

#### 2. PermissionError: Nuitka cache 目录权限不足

```
PermissionError: [Errno 13] Permission denied: 'C:\Users\...\Nuitka\Cache\...'
```

**原因**：默认缓存目录在用户目录下，可能权限受限。

**解决**：脚本已设置 `NUITKA_CACHE_DIR` 为项目本地目录。

#### 3. UPX CantPackException: GUARD_CF enabled

```
upx: qt6core.dll: CantPackException: GUARD_CF enabled PE files are not supported
```

**原因**：部分 DLL 启用了 Control Flow Guard 保护，UPX 无法压缩。

**解决**：最终方案不使用 UPX，此问题不再出现。

#### 4. 编译后 exe 启动报错: 找不到模块

**原因**：`--nofollow-import-to` 排除了运行时需要的模块。

**解决**：检查错误日志，将需要的模块改为 `--include-module`。

### 部署到目标服务器

将 `dist/CloudPortalService.exe` 复制到目标 Windows 服务器即可运行。无需安装 Python 或任何依赖。

---

## 开发环境运行

### 方式一：使用启动脚本

双击 `run.bat` 文件，脚本会自动：
1. 创建Python虚拟环境
2. 安装所需依赖
3. 启动GUI服务

### 方式二：手动运行

```bash
pip install -r requirements.txt
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
5. 编译产物为单文件 exe，运行时自动解压到临时目录

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

### 编译后 exe 启动失败
- 确认 exe 文件完整（大小 ~95 MB）
- 检查临时目录是否有写入权限
- 尝试以管理员身份运行

## 文件说明

| 文件 | 说明 |
|------|------|
| main.py | GUI主程序 |
| api_server.py | Flask API服务 |
| portal_client.py | 云门户客户端 |
| session_manager.py | 会话管理器 |
| network_utils.py | 网络工具 |
| config.py | 配置管理 |
| captcha_ocr.py | 验证码OCR识别 (ddddocr) |
| ai_audit_client.py | AI审核客户端 |
| result_types.py | 结果类型定义 |
| build_onefile_opt.py | Nuitka+zstandard 自动化编译脚本 |
| requirements.txt | Python依赖列表 |
| service_config.json | 服务配置文件 |
