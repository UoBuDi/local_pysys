# WebSocket API 文档

---

## 一、概述

### 1.1 服务说明

后端WebSocket服务提供实时双向通信能力，支持以下功能：
- 客户端状态监控与心跳检测
- 同步进度实时推送
- 日志实时推送

### 1.2 连接地址

| 环境 | 地址 |
|------|------|
| 开发环境 | `ws://localhost:8000` |
| 生产环境 | `ws://<服务器地址>:8000` |

### 1.3 协议版本

当前协议版本：`1.0.0`

---

## 二、端点列表

### 2.1 状态监控端点

**端点**：`/ws/status/{client_type}/{client_id}`

**说明**：用于前端和GUI客户端的状态监控与心跳检测

**路径参数**：
| 参数 | 类型 | 说明 | 可选值 |
|------|------|------|--------|
| client_type | string | 客户端类型 | `frontend`, `gui` |
| client_id | string | 客户端唯一标识 | 自定义 |

**示例**：
```
ws://localhost:8000/ws/status/frontend/frontend_1713582615_abc123
ws://localhost:8000/ws/status/gui/gui_a1b2c3d4
```

---

### 2.2 同步进度端点

**端点**：`/ws/sync-progress/`

**说明**：用于接收数据同步进度推送

**示例**：
```
ws://localhost:8000/ws/sync-progress/
```

---

### 2.3 日志推送端点

**端点**：`/ws/logs/`

**说明**：用于接收实时日志推送

**示例**：
```
ws://localhost:8000/ws/logs/
```

---

## 三、消息格式

### 3.1 基础消息格式

所有WebSocket消息遵循以下基础格式：

```json
{
  "type": "string",
  "version": "string",
  "timestamp": "string (ISO 8601)",
  "data": "object"
}
```

**字段说明**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 消息类型 |
| version | string | 是 | 协议版本号 |
| timestamp | string | 是 | 消息时间戳（ISO 8601格式） |
| data | object | 是 | 消息数据 |

---

### 3.2 消息类型列表

#### 3.2.1 连接相关

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `connected` | 服务端 → 客户端 | 连接成功通知 |
| `client_joined` | 服务端 → 所有客户端 | 新客户端加入通知 |
| `client_left` | 服务端 → 所有客户端 | 客户端离开通知 |

#### 3.2.2 心跳相关

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `heartbeat` | 客户端 → 服务端 | 心跳请求 |
| `heartbeat_ack` | 服务端 → 客户端 | 心跳响应 |
| `ping` | 客户端 → 服务端 | Ping请求 |
| `pong` | 服务端 → 客户端 | Pong响应 |

#### 3.2.3 状态相关

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `get_status` | 客户端 → 服务端 | 获取状态请求 |
| `status_response` | 服务端 → 客户端 | 状态响应 |
| `status_update` | 服务端 → 客户端 | 状态更新推送 |

#### 3.2.4 其他

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `message` | 服务端 → 客户端 | 普通消息广播 |
| `error` | 服务端 → 客户端 | 错误消息 |
| `sync_progress` | 服务端 → 客户端 | 同步进度推送 |
| `log` | 服务端 → 客户端 | 日志推送 |

---

### 3.3 消息示例

#### 3.3.1 连接成功消息

```json
{
  "type": "connected",
  "version": "1.0.0",
  "timestamp": "2026-04-20T10:30:00.000Z",
  "data": {
    "client_type": "frontend",
    "client_id": "frontend_1713582615_abc123",
    "server_time": "2026-04-20T10:30:00.000Z"
  }
}
```

#### 3.3.2 心跳消息

**客户端发送**：
```json
{
  "type": "heartbeat",
  "timestamp": "2026-04-20T10:30:30.000Z"
}
```

**服务端响应**：
```json
{
  "type": "heartbeat_ack",
  "version": "1.0.0",
  "timestamp": "2026-04-20T10:30:30.000Z",
  "data": {
    "server_time": "2026-04-20T10:30:30.000Z"
  }
}
```

#### 3.3.3 状态更新消息

```json
{
  "type": "status_update",
  "version": "1.0.0",
  "timestamp": "2026-04-20T10:30:00.000Z",
  "data": {
    "frontend_count": 5,
    "gui_count": 2,
    "frontend_clients": [
      {"client_id": "frontend_1", "last_heartbeat": "2026-04-20T10:30:00.000Z"}
    ],
    "gui_clients": [
      {"client_id": "gui_1", "last_heartbeat": "2026-04-20T10:30:00.000Z"}
    ]
  }
}
```

#### 3.3.4 错误消息

```json
{
  "type": "error",
  "version": "1.0.0",
  "timestamp": "2026-04-20T10:30:00.000Z",
  "data": {
    "code": 400,
    "message": "Invalid JSON format"
  }
}
```

#### 3.3.5 同步进度消息

```json
{
  "type": "sync_progress",
  "version": "1.0.0",
  "timestamp": "2026-04-20T10:30:00.000Z",
  "data": {
    "type": "config_update",
    "progress": 50,
    "message": "同步进行中...",
    "config": {}
  }
}
```

---

## 四、连接流程

### 4.1 连接建立

```
客户端                              服务端
  |                                  |
  |-------- WebSocket 连接 --------->|
  |                                  |
  |<------- connected 消息 ----------|
  |                                  |
  |<----- client_joined 广播 --------|
  |                                  |
```

### 4.2 心跳机制

```
客户端                              服务端
  |                                  |
  |-------- heartbeat 消息 --------->|
  |                                  |
  |<------ heartbeat_ack 消息 -------|
  |                                  |
```

**心跳间隔**：30秒

**超时处理**：如果服务端在60秒内未收到心跳，将认为客户端已断开

### 4.3 断开连接

```
客户端                              服务端
  |                                  |
  |-------- WebSocket 断开 --------->|
  |                                  |
  |<------ client_left 广播 ---------|
  |                                  |
```

### 4.4 重连机制

客户端应在以下情况下尝试重连：
- WebSocket连接断开
- 心跳超时
- 收到错误消息

**重连策略**：指数退避算法
- 初始延迟：1秒
- 最大延迟：30秒
- 退避因子：2

---

## 五、错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求格式错误 |
| 4000 | 无效的客户端类型 |
| 4001 | 无效的客户端ID |
| 500 | 服务端内部错误 |

---

## 六、示例代码

### 6.1 前端JavaScript示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/status/frontend/client_1');

ws.onopen = () => {
  console.log('WebSocket连接已建立');
  startHeartbeat();
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
  
  switch (message.type) {
    case 'connected':
      console.log('连接成功:', message.data);
      break;
    case 'heartbeat_ack':
      console.log('心跳响应:', message.data);
      break;
    case 'status_update':
      console.log('状态更新:', message.data);
      break;
    case 'error':
      console.error('错误:', message.data);
      break;
  }
};

ws.onclose = () => {
  console.log('WebSocket连接已关闭');
  reconnect();
};

function startHeartbeat() {
  setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'heartbeat',
        timestamp: new Date().toISOString()
      }));
    }
  }, 30000);
}

function reconnect() {
  setTimeout(() => {
    ws = new WebSocket('ws://localhost:8000/ws/status/frontend/client_1');
  }, 1000);
}
```

### 6.2 Python客户端示例

```python
import websocket
import json
import time
from datetime import datetime

def on_open(ws):
    print("WebSocket连接已建立")
    start_heartbeat(ws)

def on_message(ws, message):
    data = json.loads(message)
    print(f"收到消息: {data}")

def on_error(ws, error):
    print(f"错误: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket连接已关闭")

def start_heartbeat(ws):
    def run():
        while True:
            time.sleep(30)
            ws.send(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }))
    
    import threading
    threading.Thread(target=run, daemon=True).start()

ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws/status/gui/client_1",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
```

---

## 七、REST API

### 7.1 获取WebSocket状态

**端点**：`GET /api/ws/status`

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "frontend_count": 5,
    "gui_count": 2,
    "frontend_clients": [...],
    "gui_clients": [...]
  }
}
```

### 7.2 健康检查

**端点**：`GET /api/health`

**响应**：
```json
{
  "status": "healthy",
  "timestamp": "2026-04-20T10:30:00.000Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "message": "数据库连接正常"},
    "websocket": {"status": "healthy", "message": "WebSocket服务正常", "active_connections": 7},
    "memory": {"status": "healthy", "message": "内存使用率: 45.2%", "usage_percent": 45.2},
    "disk": {"status": "healthy", "message": "磁盘使用率: 62.1%", "usage_percent": 62.1}
  }
}
```

---

## 八、日志

### 8.1 日志文件

WebSocket连接日志保存在：`backend/logs/websocket.log`

### 8.2 日志格式

```
2026-04-20 10:30:15,123 - INFO - 连接: type=frontend, id=frontend_1713582615_abc123, ip=127.0.0.1
2026-04-20 10:30:45,456 - DEBUG - 心跳: type=frontend, id=frontend_1713582615_abc123
2026-04-20 10:31:00,789 - INFO - 断开: type=frontend, id=frontend_1713582615_abc123, reason=normal
```

### 8.3 日志轮转

- 单个日志文件最大大小：10MB
- 保留备份文件数：5
- 日志编码：UTF-8

---

## 九、注意事项

1. **客户端ID唯一性**：每个客户端应使用唯一的client_id
2. **心跳间隔**：建议客户端每30秒发送一次心跳
3. **重连策略**：使用指数退避算法，避免频繁重连
4. **消息大小**：单条消息不应超过1MB
5. **并发连接**：服务端支持最多100个并发WebSocket连接
6. **协议版本**：客户端应检查version字段以确保兼容性

---

**文档版本**：1.0.0  
**最后更新**：2026-04-20
