# 更新日志 - 2026-05-05

## 修复内容

### 1. 修复请求数量获取方式（main.py）

**问题描述**：
`fetch_request_logs` 方法中直接导入不存在的 `request_log` 变量，导致请求数量始终显示为 0。

**修复前**：
```python
from api_server import request_log
self.request_count_label.setText(str(len(request_log)))
```

**修复后**：
```python
from api_server import get_request_logger
request_log = get_request_logger().get_request_logs()
self.request_count_label.setText(str(len(request_log)))
```

**技术说明**：
- `api_server.py` 中没有全局变量 `request_log`
- 请求日志存储在 `RequestLogger` 单例的私有属性 `_request_log` 中
- 通过 `get_request_logger().get_request_logs()` 正确获取请求日志列表

### 2. 添加异常保护（main.py）

**问题描述**：
`fetch_request_logs` 方法中访问 `session_manager.last_request_time` 和 `session_manager.idle_threshold` 时，由于这些属性在 `SessionManager` 中未定义，会抛出 `AttributeError`，导致整个状态面板更新中断。

**修复内容**：
将整个 `fetch_request_logs` 方法体包裹在 `try-except` 块中：

```python
def fetch_request_logs(self):
    from session_manager import session_manager
    from api_server import get_request_logger
    import time
    
    try:
        # ... 原有状态更新逻辑 ...
    except Exception as e:
        logger.error(f"更新状态面板失败: {e}", exc_info=True)
```

**技术说明**：
- 防止单个字段缺失导致整个面板无法更新
- 异常信息记录到日志，便于后续排查
- 符合项目规则第17条：不得吞掉异常

## 代码审查

### 上下文分析

**文件**：`main.py` 第 1108-1144 行

**调用链**：
1. `on_service_started()` 创建 `QTimer`，每 2 秒触发 `fetch_request_logs()`
2. `fetch_request_logs()` 更新 5 个状态标签：
   - `heartbeat_status_label` — 心跳状态
   - `request_count_label` — 请求数量
   - `idle_countdown_label` — 空闲倒计时
   - `frontend_count_label` — 前端在线（由 WebSocket 状态更新）
   - `gui_count_label` — GUI在线（由 WebSocket 状态更新）

**剩余已知问题**：
- `session_manager.heartbeat_success_count` 和 `heartbeat_failure_count` 硬编码返回 0
- `session_manager.last_request_time` 和 `idle_threshold` 属性未定义
- 前端在线/GUI在线数据依赖后端 WebSocket 推送

## 验证建议

1. 重启 GUI 服务
2. 观察状态详情面板的请求数量是否正常统计
3. 检查日志文件是否有异常记录
4. 后续需修复 `SessionManager` 的心跳统计和空闲计时属性
