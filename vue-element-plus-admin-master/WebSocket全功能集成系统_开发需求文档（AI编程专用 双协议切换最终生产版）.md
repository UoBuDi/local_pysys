# WebSocket全功能集成系统\_开发需求文档（AI编程专用 双协议切换最终生产版）

# 1. 文档说明

本文档为**面向AI编程模型专用开发需求**，语言直白、无冗余文案，全部为硬性开发要求。本项目统一采用**WebSocket**作为唯一长连接方案，**不使用SSE、不使用轮询**。本系统支持**ws\://明文、wss\://加密双协议共存**，协议切换权限仅对后台管理员开放，前端不可硬编码协议，动态拉取服务端配置。兼顾本地开发、内网部署、公网生产、小程序、APP全环境适配。

项目定位：多端互通、高实时、双向通信、企业级协同后台系统、生产级安全加密、可自由切换通信协议。

# 2. 项目总体技术要求（硬性约束、不可改动）

- **通信方案：强制使用WebSocket，支持ws明文、wss加密双协议共存**，协议不由前端决定，由后端管理员后台配置控制。
- **实时等级：超低毫秒级延迟**，满足白板、协同编辑高频操作。
- \*\*客户端覆盖：Web端 + 小程序 + APP（Uniapp/原生）\*\*三端统一适配双协议模式。
- **数据更新模式：所有表格数据必须无感局部更新**，禁止整页刷新、禁止重载列表。
- **连接要求：自带心跳检测、断线自动重连、消息补发、异常重连机制、SSL异常捕获、协议切换重连逻辑**。
- **传输格式：统一JSON格式，支持文本、二进制、图片、文件流**，wss模式自动TLS加密，ws模式明文传输。
- **并发性能：单机稳定承载100人以内在线协同，搭配乐观锁+协作标记，低资源占用、低性能损耗**。
- **权限约束：协议切换权限仅后台管理员拥有，普通用户无权限修改通信协议**。

# 3. 基础核心能力（WebSocket底层必须封装、含双协议切换）

## 3.1 双协议配置规范（AI重点开发）

- 后端新增全局系统配置项：**websocket\_protocol**，可选枚举值：`ws`、`wss`。
- 后台管理页面提供可视化开关，管理员一键切换协议，配置**无需重启服务、实时生效**。
- 后端提供公共无鉴权接口，前端初始化必须优先请求接口，动态获取当前WebSocket完整连接地址，**禁止前端硬编码协议、域名、端口**。
- 后端服务同时兼容HTTP+WS、HTTPS+WSS服务能力，双服务并行就绪。
- SSL证书独立配置管理，仅wss模式加载证书；ws模式不加载证书，减少服务器资源开销。
- 使用场景划分：内网/局域网/本地测试使用ws；公网/生产/小程序/对外环境使用wss。
- 协议切换联动：修改协议配置后，所有在线用户自动断线、自动重连至新协议地址。
- 平台兼容限制：小程序强制要求加密协议，管理员切换为ws模式时，小程序端提示当前环境不可用。
- 生产环境约束：生产环境推荐永久锁定wss，仅测试环境可自由切换ws。

## 3.2 WSS加密协议强制规范

- wss模式下彻底禁用明文传输，全部走TLS加密链路。
- 后端必须搭载正规SSL证书，证书格式支持pem、crt、key。
- 生产环境开启强制SSL校验，禁止忽略不安全证书、禁止关闭证书校验。
- 支持Nginx反向代理WSS，后端识别代理真实客户端IP。
- 全站HTTP强制301跳转HTTPS，杜绝浏览器混合内容安全拦截报错。

## 3.3 连接管理

- 建立连接时携带Token鉴权，非法连接直接断开。
- 绑定用户ID、设备类型、登录终端。
- 心跳机制：前端定时发送心跳包，后端检测死连接并清除。
- 断网、刷新、网络抖动、SSL证书异常、协议变更自动重连，重连后恢复会话状态。
- 连接状态可视化：连接中、已连接、断开、重连中、SSL异常、协议不匹配。
- 分类捕获异常：明文连接失败、SSL握手失败、证书过期、域名拦截、跨域失败。

## 3.4 消息通用格式（双协议通用、格式不变）

所有WebSocket传输报文必须遵循以下结构，加密层由WSS自动处理，业务层无需改动：

```json
{
  "type": "业务指令类型",
  "fromUserId": "发送人ID",
  "toUserId": "接收人ID(可为空)",
  "roomId": "房间/群组ID(可为空)",
  "data": {},
  "timestamp": 时间戳
}
```

## 3.5 房间分组机制

- 支持单人私聊房间、多人群组房间、协同编辑房间、白板房间。
- 消息隔离：不同房间消息互不干扰。
- 支持用户主动加入、退出、销毁房间。

# 4. 业务功能需求清单（全部保留、无改动、兼容双协议）

## 4.1 数据表无感实时更新（基础核心）

适用于后台管理系统所有数据表格。

- 多用户环境下，任意一端新增、修改、删除数据，其他用户**无刷新、无重载、无感局部更新**。
- 只更新变更行，保留分页、筛选、排序、勾选、滚动条位置。
- **采用乐观锁+WebSocket协作标记**：行级编辑状态标记、前端提前锁定、后端版本号兜底防冲突。
- 实时推送操作日志，全员可视。

## 4.2 在线聊天系统

- 一对一私聊、多人群聊。
- 支持文字、表情包、图片、文件传输。
- 消息已读、未读、撤回、删除。
- 在线状态：上线、离线、离开。
- 会话列表实时同步。
- **悬浮聊天入口图标**：前端页面右下角始终显示悬浮图标，点击打开/缩小聊天窗口，图标支持拖拽移动位置，拖拽后自动吸附屏幕边缘，位置持久化记忆，未读消息红点提示，连接状态光晕指示。

## 4.3 多人协同编辑

- 支持在线富文本、表单、在线表格协同编辑。
- 多人同时编辑，操作互不冲突。
- 光标位置同步、编辑人标识显示。
- 数据差分更新，降低传输流量。

## 4.4 在线白板

- 画笔、橡皮擦、直线、矩形、圆形、文字标注。
- 笔迹实时同步，超低延迟。
- 画布清空、撤销、恢复。
- 支持图片背景、图片插入。
- 高频操作节流防抖，防止卡顿。

## 4.5 多端互通能力（Web + 小程序 + APP）

- 三端消息互通、会话同步，**小程序强制适配wss域名安全校验**。
- 多设备登录互斥、强制下线。
- APP后台保活长连接，离线上线消息同步。
- 三端统一跟随后端配置协议，不允许任意一端私自固定协议。

## 4.6 系统实时通知与管控

- 全站弹窗通知、站内消息、审批流实时推送。
- 后端可主动下发指令，强制刷新前端权限、菜单、按钮。
- 后台可实时踢出指定在线用户。
- 在线人数、在线设备实时统计。

## 4.7 大屏可视化实时监控

- 大屏图表、数据看板实时刷新。
- 服务器CPU、内存、带宽状态实时推送。
- 异常告警弹窗提示。

# 5. 乐观锁+WebSocket协作标记 性能约束（100人并发量化指标）

## 5.1 性能指标（硬性标准）

- 最大在线并发人数：100人稳定在线。
- 服务器硬件最低配置：1核2G云服务器即可运行。
- CPU平均占用：≤15%，峰值不超过25%。
- 内存占用：WS空闲连接单连接约10KB\~16KB，整体内存占用极低。
- 数据库：采用MySQL乐观锁version机制，无锁表、无阻塞，QPS维持低位数。
- 协作标记：编辑状态优先内存存储，减少数据库压力，前端提前拦截冲突。
- 消息推送：仅推送变更行、变更状态，禁止全量广播。
- 全网平均延迟：≤50ms，满足超低毫秒级实时交互。

# 6. 非功能性需求（AI必须严格遵守）

- **禁止页面刷新**：所有数据更新必须DOM局部更新。
- **低延迟**：平均延迟控制在50ms以内。
- **高并发**：支持单服务100人在线稳定连接。
- **容错性**：断网、闪退、刷新、SSL异常、协议切换不丢失未发送消息。
- **解耦封装**：WebSocket单独封装工具类，业务层与连接层分离。
- **可拓展**：后续可新增直播、物联网设备控制、游戏互动模块。
- **业务一致性**：ws、wss两种模式业务逻辑完全一致，仅底层加密区别。

# 7. 明确排除项（禁止开发）

- 禁止使用SSE、长轮询替代WebSocket。
- 禁止使用第三方商用即时通讯SDK，全部自研。
- 禁止表格整体重载，必须行级更新。
- 禁止前端硬编码WebSocket协议与地址。
- 禁止普通用户手动修改协议模式。
- 禁止生产环境随意关闭SSL证书校验。

# 8. 交付要求（给AI开发指令）

1. 后端开发协议配置管理模块，实现管理员后台可视化一键切换ws/wss。
2. 开发公共配置接口，前端动态拉取WebSocket连接地址。
3. 输出前端通用WebSocket封装类，自带**双协议自适应、SSL异常捕获、自动重连**。
4. 输出后端WebSocket服务类，兼容双协议、SSL证书、Nginx反向代理。
5. 输出数据表无感更新标准示例代码，内含乐观锁+协作标记完整逻辑。
6. 输出聊天、白板、协同编辑最小demo，全部兼容ws/wss双协议。
7. 附带内网ws部署、公网wss证书部署、Nginx双协议标准配置文件。
8. 代码注释详细、结构分层、通俗易懂、便于二次扩展、可直接上线部署。

> （注：文档部分内容可能由 AI 生成）

***

# 9. 未实现功能清单与开发计划

## 9.0 当前已实现功能基线

| 模块            | 已实现                                                              | 代码位置                                     |
| ------------- | ---------------------------------------------------------------- | ---------------------------------------- |
| WebSocket连接管理 | ✅ `StatusConnectionManager` 支持前端/GUI双通道                          | `backend/core/websocket_manager.py`      |
| WebSocket端点   | ✅ `/ws/status/{client_type}/{client_id}`                         | `backend/routers/websocket_endpoints.py` |
| 心跳机制          | ✅ 前端30s心跳 + 后端heartbeat\_ack                                     | `src/utils/websocket.ts`                 |
| 断线重连          | ✅ 指数退避重连（3s→30s，最多5次）                                            | `src/utils/websocket.ts`                 |
| 连接状态可视化       | ✅ Footer显示连接状态+在线人数                                              | `src/components/Footer/src/Footer.vue`   |
| 消息广播          | ✅ `broadcast_to_frontend` / `broadcast_to_gui` / `broadcast_all` | `backend/core/websocket_manager.py`      |
| REST状态查询      | ✅ `/api/ws/status` / `/api/ws/stats`                             | `backend/routers/websocket_endpoints.py` |
| 数据表格CRUD      | ✅ 拆分匹配的查询/更新/导出/导入                                               | `backend/routers/split_match.py`         |
| 前端WebSocket封装 | ✅ `WebSocketService` 单例 + `useWebSocket` composable              | `src/utils/websocket.ts`                 |

## 9.1 未实现功能完整清单

| 编号   | 功能                | 对应需求章节          | 优先级 | 当前状态                |
| ---- | ----------------- | --------------- | --- | ------------------- |
| F-01 | 乐观锁版本管理           | 4.1 / 5.1       | P0  | ❌ 完全未实现             |
| F-02 | 行级协作锁（内存存储+前端锁定）  | 4.1 / 5.1       | P0  | ❌ 完全未实现             |
| F-03 | 数据表无感局部更新         | 4.1 / 6         | P0  | ❌ 当前保存后整表刷新         |
| F-04 | 协作事件广播+消息格式+房间机制  | 3.4 / 3.5 / 4.1 | P0  | ❌ 广播未实现+消息格式缺字段+无房间 |
| F-05 | 编辑历史/操作日志         | 4.1             | P1  | ❌ 完全未实现             |
| F-06 | WebSocket Token鉴权 | 3.3             | P1  | ❌ 当前WebSocket无鉴权    |
| F-07 | 双协议(ws/wss)配置管理   | 3.1             | P2  | ❌ 前端硬编码协议推断         |
| F-08 | 连接状态增强（6种状态可视化）   | 3.3             | P2  | ⚠️ 仅已连接/未连接两种       |
| F-09 | 在线聊天系统（文字+文件）     | 4.2             | P3  | ❌ 完全未实现             |
| F-10 | 多人协同编辑（行级锁扩展）     | 4.3             | P3  | ❌ 完全未实现             |
| F-11 | 系统实时通知与管控         | 4.6             | P3  | ❌ 完全未实现             |

> **精简说明**：原F-06（消息格式对齐）和F-07（房间机制）已合并入F-04，因三者互为前置依赖；原F-11（消息补发）已移除，断线重连后由业务层自行刷新数据即可；原F-14（在线白板）已移出开发计划，标记为未来扩展；原F-16（大屏监控）已移出开发计划，使用现有运维工具替代；F-09（原F-12聊天）简化为文字+文件；F-10（原F-13协同编辑）简化为行级锁扩展；F-11（原F-15通知）简化为推送通知。

***

## 9.2 F-01：乐观锁版本管理（P0）

### 需求描述

采用MySQL乐观锁version机制，无锁表、无阻塞。版本号存储在独立表中，不修改月度表（\*\_yc）结构。

### 数据库设计

在 `system_db` 中新建 `row_versions` 表：

```sql
CREATE TABLE IF NOT EXISTS row_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL COMMENT '月度表名，如 2025-12_yc',
    row_id VARCHAR(100) NOT NULL COMMENT '月度表中的通行标识ID',
    version INT NOT NULL DEFAULT 1 COMMENT '乐观锁版本号',
    updated_by VARCHAR(100) DEFAULT NULL COMMENT '最后修改者用户名',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_table_row (table_name, row_id),
    INDEX idx_table_name (table_name),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行版本管理表（乐观锁）';
```

### 后端开发方案

**新建文件**：`backend/services/collaboration_service.py`

```python
async def get_or_create_version(table_name: str, row_id: str) -> dict:
    """获取行版本号，不存在则创建（懒初始化）"""
    # SELECT version, updated_by, updated_at FROM row_versions
    #   WHERE table_name=%s AND row_id=%s
    # 若不存在 → INSERT row_versions(version=1)
    # 返回 {"version": N, "updated_by": "xxx", "updated_at": "..."}

async def increment_version(table_name: str, row_id: str, username: str) -> int:
    """版本号+1，返回新版本号"""
    # UPDATE row_versions SET version=version+1, updated_by=%s, updated_at=NOW()
    #   WHERE table_name=%s AND row_id=%s
    # 若影响行数=0 → INSERT row_versions(version=2, updated_by=%s)
    # 返回新版本号
```

**修改文件**：`backend/routers/split_match.py`

- 修改 `update_split_match_data` 端点，增加乐观锁校验逻辑：
  1. 请求体新增 `version`（可选）和 `force_overwrite`（可选）字段
  2. 更新前查询 `row_versions` 获取当前版本号
  3. 若 `version` 不匹配且非强制覆盖 → 返回 `code:409` + 冲突信息
  4. 更新成功后调用 `increment_version`

**新增端点**：`GET /api/split-match/row-version/`

- 参数：`table_name` + `row_id`
- 返回：`{version, updated_by, updated_at}`

**修改文件**：`backend/core/models.py`

- `UpdateMatchRequest` 新增字段：`version: Optional[int] = None`、`force_overwrite: Optional[bool] = False`

### 前端开发方案

**修改文件**：`src/api/split-match/index.ts`

- `updateSplitMatchData` 参数新增 `version?` 和 `force_overwrite?`
- 新增 `getRowVersion(params)` API函数

**修改文件**：`src/views/SystemTools/SplitMatch.vue`

- 打开编辑对话框时获取当前版本号
- 保存时携带版本号
- 处理409冲突响应

### 数据流时序

```
用户点击编辑 → 获取当前版本号(version=N) → 打开编辑对话框
用户保存 → 提交{data, version=N} → 后端校验版本
  ├─ 版本匹配 → 更新数据 + 版本+1 → 返回200
  └─ 版本不匹配 → 返回409 + 当前修改者 → 前端弹出冲突对话框
```

***

## 9.3 F-02：行级协作锁（P0）

### 需求描述

行级编辑状态标记、前端提前锁定、后端版本号兜底防冲突。编辑状态优先内存存储，减少数据库压力。服务重启时锁自动清除，用户重新编辑即可重新加锁。

### 设计决策：内存存储 vs 数据库存储

| 维度   | 内存存储            | 数据库存储         |
| ---- | --------------- | ------------- |
| 性能   | 纯字典操作，零SQL开销    | 每次加锁/解锁需SQL查询 |
| 可靠性  | 服务重启锁清除（可接受）    | 持久化，重启不丢失     |
| 复杂度  | 简单，无需建表         | 需建表+过期清理+索引维护 |
| 适用场景 | 100人内部系统，锁为临时状态 | 需要跨重启保持锁状态    |

**结论**：采用内存存储。锁本质是临时状态（5分钟过期），服务重启后所有用户重新编辑即可，无需持久化。

### 后端开发方案

**扩展文件**：`backend/core/websocket_manager.py`

在 `StatusConnectionManager` 中新增内存锁管理：

```python
class StatusConnectionManager:
    def __init__(self):
        # ... 现有属性 ...
        self.row_locks: Dict[str, Dict] = {}
        # key: f"{table_name}:{row_id}"
        # value: {
        #     "user_id": int,
        #     "username": str,
        #     "locked_at": datetime,
        #     "expires_at": datetime
        # }

    def acquire_row_lock(self, table_name: str, row_id: str,
                         user_id: int, username: str) -> dict:
        """获取行锁（内存操作）"""
        from datetime import datetime, timedelta
        key = f"{table_name}:{row_id}"
        now = datetime.now()

        # 清理该key的过期锁
        if key in self.row_locks and self.row_locks[key]["expires_at"] < now:
            del self.row_locks[key]

        if key in self.row_locks:
            existing = self.row_locks[key]
            if existing["user_id"] == user_id:
                # 续期5分钟
                existing["expires_at"] = now + timedelta(minutes=5)
                return {"locked": True, "own_lock": True}
            else:
                # 已被他人锁定
                return {
                    "locked": False,
                    "own_lock": False,
                    "locked_by": existing["username"],
                    "user_id": existing["user_id"]
                }

        # 无锁，新建
        self.row_locks[key] = {
            "user_id": user_id,
            "username": username,
            "locked_at": now,
            "expires_at": now + timedelta(minutes=5)
        }
        return {"locked": True, "own_lock": True}

    def release_row_lock(self, table_name: str, row_id: str, user_id: int) -> bool:
        """释放行锁（仅锁持有者可释放）"""
        key = f"{table_name}:{row_id}"
        if key in self.row_locks and self.row_locks[key]["user_id"] == user_id:
            del self.row_locks[key]
            return True
        return False

    def get_active_locks(self, table_name: str) -> list:
        """获取指定表的所有活跃锁"""
        from datetime import datetime
        now = datetime.now()
        result = []
        prefix = f"{table_name}:"
        expired_keys = []
        for key, lock in self.row_locks.items():
            if key.startswith(prefix):
                if lock["expires_at"] < now:
                    expired_keys.append(key)
                else:
                    result.append({
                        "row_id": key[len(prefix):],
                        "user_id": lock["user_id"],
                        "username": lock["username"],
                        "expires_at": lock["expires_at"].isoformat()
                    })
        for k in expired_keys:
            del self.row_locks[k]
        return result

    def force_release_lock(self, table_name: str, row_id: str) -> bool:
        """强制释放锁（管理员导入时使用）"""
        key = f"{table_name}:{row_id}"
        if key in self.row_locks:
            del self.row_locks[key]
            return True
        return False

    def cleanup_expired_locks(self):
        """清理所有过期锁（可由心跳或定时任务调用）"""
        from datetime import datetime
        now = datetime.now()
        expired = [k for k, v in self.row_locks.items() if v["expires_at"] < now]
        for k in expired:
            del self.row_locks[k]
```

**新增端点**：

| 端点                               | 方法   | 请求体                                   | 返回                                               |
| -------------------------------- | ---- | ------------------------------------- | ------------------------------------------------ |
| `/api/split-match/lock/`         | POST | `{table_name, row_id}` + user\_id查询参数 | `{code, data: {locked, own_lock, locked_by?}}`   |
| `/api/split-match/unlock/`       | POST | `{table_name, row_id}` + user\_id查询参数 | `{code, message}`                                |
| `/api/split-match/active-locks/` | GET  | `table_name`查询参数                      | `{code, data: [{row_id, username, expires_at}]}` |

**修改文件**：`backend/routers/split_match.py`

锁操作直接调用 `status_manager.acquire_row_lock` / `release_row_lock` / `get_active_locks`，无需数据库查询。

**修改文件**：`backend/core/models.py`

- 新增 `LockRequest(BaseModel)`：`table_name: str`、`row_id: str`
- 新增 `UnlockRequest(BaseModel)`：`table_name: str`、`row_id: str`

### 前端开发方案

**修改文件**：`src/api/split-match/index.ts`

```typescript
export const lockRow = (data: { table_name: string; row_id: string }, userId?: number) => {
  return request.post({ url: appendUserId('/api/split-match/lock/', userId), data })
}

export const unlockRow = (data: { table_name: string; row_id: string }, userId?: number) => {
  return request.post({ url: appendUserId('/api/split-match/unlock/', userId), data })
}

export const getActiveLocks = (tableName: string) => {
  return request.get({ url: '/api/split-match/active-locks/', params: { table_name: tableName } })
}
```

**修改文件**：`src/views/SystemTools/SplitMatch.vue`

- `handleIdClick` 改为先请求锁，再决定打开可编辑/只读对话框
- `handleDialogClose` 时释放锁
- 新增 `currentLockedRowId` ref 追踪当前锁定的行
- 表格行根据 `activeLocks` 数据显示编辑者标记

### 协作标记层行级显示需求

拆分匹配页面数据表中的每一行必须在行级别直观显示协作状态，确保所有用户一眼即可识别哪些行正在被编辑。

**行级协作标记规范**：

| 标记项 | 要求 | 说明 |
| ---- | ---- | ---- |
| 行背景色 | 被锁定行整体变色 | 自己锁定的行：浅绿色（`#f0f9eb`）；他人锁定的行：浅黄色（`#fdf6ec`） |
| 锁图标 | 通行标识ID列显示锁图标 | 他人锁定的行显示黄色锁图标，tooltip提示"XX 正在编辑" |
| 状态标签 | 编辑对话框标题栏显示状态 | "已锁定（编辑中）"绿色标签（自己锁定）；"XX 正在编辑"黄色标签（他人锁定） |
| 行样式优先级 | 行背景色高于表格stripe | 使用 `!important` 确保锁定行背景色不被stripe覆盖 |
| 实时更新 | 锁定/解锁时行样式即时变化 | 通过WebSocket `row_locked`/`row_unlocked` 事件驱动 `activeLocksMap` 更新 |

**实现方式**：

- `el-table` 绑定 `:row-class-name="getRowClassName"` 方法
- `getRowClassName` 根据 `activeLocksMap` 判断当前行是否被锁定，返回 `row-locked-self`（自己锁定）或 `row-locked-other`（他人锁定）
- CSS 样式通过 `::deep()` 穿透到 `el-table` 行元素

### 锁策略

| 参数    | 值                      | 理由                   |
| ----- | ---------------------- | -------------------- |
| 存储方式  | 内存字典                   | 零SQL开销，锁为临时状态无需持久化   |
| 锁过期时间 | 5分钟                    | 平衡安全性与用户体验           |
| 续期策略  | 同一用户再次请求时自动续期          | 避免长时间编辑中锁过期          |
| 过期清理  | acquire时按需清理 + 心跳时批量清理 | 无需独立定时任务             |
| 服务重启  | 锁自动清除                  | 用户重新编辑即可重新加锁，无副作用    |
| 管理员导入 | 强制释放锁+直接更新             | 符合需求4"导入操作允许管理员强制覆盖" |

***

## 9.4 F-03：数据表无感局部更新（P0）

### 需求描述

多用户环境下，任意一端新增、修改、删除数据，其他用户无刷新、无重载、无感局部更新。只更新变更行，保留分页、筛选、排序、勾选、滚动条位置。禁止整页刷新、禁止重载列表。

### 当前问题

保存成功后调用 `loadTableData()` 整表刷新，违反文档6"禁止页面刷新"要求。

### 后端开发方案

**新增端点**：`GET /api/split-match/row/`

- 参数：`table_name` + `row_id`
- 返回：该行的完整数据（单行查询）
- 用途：其他用户收到 `row_updated` 事件后，请求该行最新数据

```python
@router.get("/api/split-match/row/")
async def get_single_row(
    table_name: str = Query(...),
    row_id: str = Query(...),
    user: dict = Depends(get_current_user)
):
    """获取单行数据（用于协作局部更新）"""
    # SELECT * FROM `{table_name}` WHERE `通行标识ID` = %s
    # 排除BLOB列，仅返回文本列
```

### 前端开发方案

**修改文件**：`src/views/SystemTools/SplitMatch.vue`

1. **移除** **`loadTableData()`** **整表刷新**

   保存成功后改为局部更新：
   ```typescript
   // 旧代码（整表刷新）
   loadTableData().catch(e => console.error('保存后刷新表格失败:', e))

   // 新代码（局部更新）
   updateSingleRowInTable(selectedTable.value, rowId)
   ```
2. **新增** **`updateSingleRowInTable`** **方法**
   ```typescript
   const updateSingleRowInTable = async (tableName: string, rowId: string) => {
     const resp = await getSingleRow({ table_name: tableName, row_id: rowId })
     if (resp?.code === 200 && resp.data) {
       const rowIndex = tableData.value.findIndex(
         row => String(row['通行标识ID']) === rowId
       )
       if (rowIndex !== -1) {
         tableData.value[rowIndex] = { ...tableData.value[rowIndex], ...resp.data }
       }
     }
   }
   ```
3. **WebSocket驱动的局部更新**

   收到 `row_updated` 事件时调用 `updateSingleRowInTable`
4. **保留滚动位置**
   ```typescript
   const tableRef = ref()
   const savedScrollTop = ref(0)

   // 更新前保存滚动位置
   const scrollTop = tableRef.value?.scrollBarRef?.wrapRef?.scrollTop
   if (scrollTop) savedScrollTop.value = scrollTop

   // 更新后恢复滚动位置
   await nextTick()
   if (savedScrollTop.value) {
     tableRef.value?.scrollBarRef?.wrapRef?.scrollTo({ top: savedScrollTop.value })
   }
   ```
5. **保留分页、筛选、排序、勾选状态**

   局部更新仅替换 `tableData` 中对应行的数据，不影响其他状态变量。

### 数据流时序

```
用户A保存 → 后端更新数据 → WebSocket广播row_updated → 用户B前端收到事件
  → 用户B调用getSingleRow获取最新数据 → 原地替换tableData中对应行
  → 滚动位置不变、分页不变、筛选不变
```

***

## 9.5 F-04：协作事件广播+消息格式+房间机制（P0）

### 需求描述

1. 仅推送变更行、变更状态，禁止全量广播。协作事件按表房间隔离，不同月度表互不干扰。
2. 所有WebSocket传输报文必须遵循文档3.4节定义的统一格式（含fromUserId/toUserId/roomId/timestamp）。
3. 支持协作编辑房间、私聊房间、群聊房间。消息隔离：不同房间消息互不干扰。支持用户主动加入、退出房间。

> **合并说明**：原F-06（消息格式对齐）和F-07（房间机制）是协作广播的前置依赖，必须同步实现，因此合并为本章节。

### 后端开发方案

**修改文件**：`backend/core/websocket_manager.py`

新增消息构建、房间管理和协作广播方法：

```python
import time
import json
from typing import Dict, Optional

class StatusConnectionManager:
    def __init__(self):
        # ... 现有属性 ...
        self.rooms: Dict[str, Dict] = {}
        # rooms 结构：
        # {
        #   "collab_2025-12_yc": {
        #       "type": "collaboration",
        #       "members": {"client_id_1": {"user_id": 1, "username": "admin"}, ...}
        #   },
        #   "chat_1_3": {
        #       "type": "private_chat",
        #       "members": {...}
        #   }
        # }

    @staticmethod
    def build_message(msg_type: str, data: dict = None,
                      from_user_id: int = None, to_user_id: int = None,
                      room_id: str = None) -> dict:
        """构建符合文档3.4规范的WebSocket消息"""
        return {
            "type": msg_type,
            "fromUserId": from_user_id,
            "toUserId": to_user_id,
            "roomId": room_id,
            "data": data or {},
            "timestamp": int(time.time() * 1000)
        }

    async def join_room(self, client_id: str, room_id: str, user_info: dict = None):
        """用户加入房间"""
        if room_id not in self.rooms:
            self.rooms[room_id] = {"type": "collaboration", "members": {}}
        self.rooms[room_id]["members"][client_id] = user_info or {}

    async def leave_room(self, client_id: str, room_id: str):
        """用户离开房间"""
        if room_id in self.rooms and client_id in self.rooms[room_id]["members"]:
            del self.rooms[room_id]["members"][client_id]
            if not self.rooms[room_id]["members"]:
                del self.rooms[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict):
        """向房间内所有用户广播消息"""
        if room_id not in self.rooms:
            return
        msg_str = json.dumps(message)
        offline_clients = []
        for client_id in self.rooms[room_id]["members"]:
            conn = self._find_connection(client_id)
            if conn:
                try:
                    await conn["websocket"].send_text(msg_str)
                except Exception:
                    continue
        # 注意：广播失败仅记录日志，不影响业务结果

    async def broadcast_collaboration(self, message: dict):
        """广播协作事件（按房间隔离）"""
        room_id = message.get("roomId", "")
        if room_id:
            await self.broadcast_to_room(room_id, message)
        else:
            await self.broadcast_to_frontend(message)

    def get_room_members(self, room_id: str) -> list:
        """获取房间成员列表"""
        if room_id not in self.rooms:
            return []
        return list(self.rooms[room_id]["members"].values())

    def get_user_rooms(self, client_id: str) -> list:
        """获取用户所在的所有房间"""
        return [rid for rid, room in self.rooms.items()
                if client_id in room["members"]]
```

**修改文件**：`backend/routers/websocket_endpoints.py`

新增房间管理消息类型，所有消息使用 `build_message` 构建：

```python
# WebSocket消息处理中新增
elif message.get("type") == "join_room":
    room_id = message.get("roomId", "")
    user_info = {"user_id": user_id, "username": username}
    await status_manager.join_room(client_id, room_id, user_info)

elif message.get("type") == "leave_room":
    room_id = message.get("roomId", "")
    await status_manager.leave_room(client_id, room_id)

elif message.get("type") == "get_room_members":
    room_id = message.get("roomId", "")
    members = status_manager.get_room_members(room_id)
    await websocket.send_text(json.dumps(
        status_manager.build_message("room_members", {"members": members}, room_id=room_id)
    ))
```

**修改文件**：`backend/routers/split_match.py`

在锁/解锁/更新操作后使用 `build_message` 广播协作事件：

```python
from core.websocket_manager import status_manager

# 加锁成功后
await status_manager.broadcast_collaboration(
    status_manager.build_message(
        "row_locked",
        {"table_name": table_name, "row_id": row_id, "username": username},
        from_user_id=user_id,
        room_id=f"collab_{table_name}"
    )
)

# 解锁后
await status_manager.broadcast_collaboration(
    status_manager.build_message(
        "row_unlocked",
        {"table_name": table_name, "row_id": row_id},
        from_user_id=user_id,
        room_id=f"collab_{table_name}"
    )
)

# 更新成功后
await status_manager.broadcast_collaboration(
    status_manager.build_message(
        "row_updated",
        {"table_name": table_name, "row_id": row_id, "username": username},
        from_user_id=user_id,
        room_id=f"collab_{table_name}"
    )
)
```

### 前端开发方案

**修改文件**：`src/utils/websocket.ts`

新增协作事件回调类型、房间管理和统一消息格式：

```typescript
export type CollabEventType = 'row_locked' | 'row_unlocked' | 'row_updated' | 'row_conflict'

export interface CollabEvent {
  type: CollabEventType
  fromUserId: number
  toUserId?: number
  roomId: string
  data: {
    table_name: string
    row_id: string
    user_id?: number
    username?: string
    version?: number
  }
  timestamp: number
}

export type CollaborationCallback = (event: CollabEvent) => void

// WsMessage 接口新增字段
export interface WsMessage {
  type: string
  fromUserId?: number
  toUserId?: number
  roomId?: string
  data?: any
  timestamp?: number
}

// WebSocketService 类新增
private collaborationCallback: CollaborationCallback | null = null
private currentRoomId: string | null = null

onCollaboration(callback: CollaborationCallback) {
  this.collaborationCallback = callback
}

joinRoom(roomId: string) {
  this.currentRoomId = roomId
  this.send({ type: 'join_room', roomId })
}

leaveRoom(roomId: string) {
  this.currentRoomId = null
  this.send({ type: 'leave_room', roomId })
}

getRoomMembers(roomId: string) {
  this.send({ type: 'get_room_members', roomId })
}

// onmessage 中新增处理
if (['row_locked', 'row_unlocked', 'row_updated', 'row_conflict'].includes(message.type)) {
  if (this.collaborationCallback) {
    this.collaborationCallback(message as CollabEvent)
  }
}
```

**修改文件**：`src/views/SystemTools/SplitMatch.vue`

- 选择表时 `joinRoom('collab_' + selectedTable)`
- 切换表时 `leaveRoom('collab_' + oldTable)` + `joinRoom('collab_' + newTable)`
- 注册 `onCollaboration` 回调处理协作事件

### 房间ID命名规范

| 房间类型 | ID格式                       | 示例                  |
| ---- | -------------------------- | ------------------- |
| 协作编辑 | `collab_{table_name}`      | `collab_2025-12_yc` |
| 私聊   | `chat_{min_uid}_{max_uid}` | `chat_1_3`          |
| 群聊   | `group_{group_id}`         | `group_101`         |

### 协作事件类型

| 事件             | 触发时机          | 广播范围     | 前端处理           |
| -------------- | ------------- | -------- | -------------- |
| `row_locked`   | 用户点击编辑→后端加锁成功 | 同表房间所有用户 | 行首显示编辑者图标+黄色背景 |
| `row_unlocked` | 用户关闭编辑/锁过期    | 同表房间所有用户 | 移除编辑者标记        |
| `row_updated`  | 用户保存成功        | 同表房间所有用户 | 局部更新该行数据       |
| `row_conflict` | 保存时版本冲突       | 仅当前操作用户  | 弹出冲突对话框        |

### 兼容策略

- `fromUserId`、`toUserId`、`roomId`、`timestamp` 均为可选字段，旧消息格式仍可正常解析
- 所有新增消息发送点统一使用 `build_message` 构建
- 广播失败仅记录日志，不影响业务结果（更新操作以数据库写入为准）

***

## 9.6 F-05：编辑历史/操作日志（P1）

### 需求描述

需要编辑历史/操作日志（谁在什么时间修改了什么）。实时推送操作日志，全员可视。

### 数据库设计

在 `system_db` 中新建 `edit_history` 表：

```sql
CREATE TABLE IF NOT EXISTS edit_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    row_id VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    username VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL DEFAULT 'update' COMMENT 'update/import/force_overwrite',
    version_before INT DEFAULT NULL,
    version_after INT DEFAULT NULL,
    changed_fields JSON DEFAULT NULL COMMENT '{"field": {"old": "x", "new": "y"}}',
    force_overwrite TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_table_row (table_name, row_id),
    INDEX idx_user (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='编辑历史记录';
```

### 后端开发方案

**扩展文件**：`backend/services/collaboration_service.py`

```python
async def record_edit_history(
    table_name: str, row_id: str, user_id: int, username: str,
    action: str = "update", version_before: int = None, version_after: int = None,
    changed_fields: dict = None, force_overwrite: bool = False
) -> int:
    """记录编辑历史"""
    # INSERT INTO edit_history (table_name, row_id, user_id, username, action,
    #   version_before, version_after, changed_fields, force_overwrite)
    # VALUES (...)

async def get_edit_history(
    table_name: str, row_id: str = None, page: int = 1, page_size: int = 20
) -> dict:
    """查询编辑历史"""
    # SELECT * FROM edit_history WHERE table_name=%s [AND row_id=%s]
    #   ORDER BY created_at DESC LIMIT offset, page_size
```

**新增端点**：`GET /api/split-match/edit-history/`

- 参数：`table_name` + `row_id`（可选）+ `page` + `page_size`
- 返回：编辑历史列表 + 总数

**修改文件**：`backend/routers/split_match.py`

- `update_split_match_data` 成功更新后调用 `record_edit_history`
- 记录 `changed_fields`：对比更新前后的字段值差异

### 前端开发方案

**修改文件**：`src/api/split-match/index.ts`

```typescript
export interface EditHistoryRecord {
  id: number
  table_name: string
  row_id: string
  user_id: number
  username: string
  action: string
  version_before: number | null
  version_after: number | null
  changed_fields: Record<string, { old: unknown; new: unknown }> | null
  force_overwrite: boolean
  created_at: string
}

export const getEditHistory = (params: {
  table_name: string
  row_id?: string
  page?: number
  page_size?: number
}) => {
  return request.get({ url: '/api/split-match/edit-history/', params })
}
```

**修改文件**：`src/views/SystemTools/SplitMatch.vue`

- 编辑对话框中新增"编辑历史"按钮
- 点击后打开历史记录抽屉/对话框
- 展示：用户名、操作时间、操作类型、变更字段（旧值→新值）
- 操作日志实时推送：收到 `row_updated` 事件时在页面底部显示提示

***

## 9.7 F-06：WebSocket Token鉴权（P1）

### 需求描述

建立连接时携带Token鉴权，非法连接直接断开。绑定用户ID、设备类型、登录终端。

> **优先级提升说明**：Token鉴权是安全基础，原为P2，现提升为P1与编辑历史同步实现。

### 后端开发方案

**修改文件**：`backend/routers/websocket_endpoints.py`

```python
@router.websocket("/ws/status/{client_type}/{client_id}")
async def websocket_status(websocket: WebSocket, client_type: str, client_id: str,
                           token: str = Query(None)):
    """带Token鉴权的WebSocket端点"""
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        from core.dependencies import decode_token
        user = decode_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Token verification failed")
        return

    user_id = user.get("id")
    username = user.get("username")
    device_type = client_type

    await status_manager.connect_frontend(websocket, client_id, user_id, username, device_type)
    # ...
```

**修改文件**：`backend/core/websocket_manager.py`

连接信息扩展：

```python
# frontend_connections 中每个连接增加用户信息
{
    "websocket": websocket,
    "client_id": client_id,
    "user_id": user_id,
    "username": username,
    "device_type": device_type,
    "last_heartbeat": datetime.now()
}
```

### 前端开发方案

**修改文件**：`src/utils/websocket.ts`

```typescript
connect(url: string = '') {
    const token = localStorage.getItem('token') || ''
    const wsUrl = `${baseUrl}/ws/status/frontend/${this.clientId}?token=${encodeURIComponent(token)}`
    this.ws = new WebSocket(wsUrl)
}
```

***

## 9.8 F-07：双协议(ws/wss)配置管理（P2）

### 需求描述

后端新增全局系统配置项 `websocket_protocol`，管理员后台可视化一键切换ws/wss，配置无需重启服务、实时生效。后端提供公共无鉴权接口，前端动态获取WebSocket连接地址，禁止前端硬编码协议、域名、端口。

### 后端开发方案

**修改文件**：`backend/config.ini`

新增配置节：

```ini
[WEBSOCKET]
protocol = ws
host = 172.32.48.238
port = 8001
ssl_cert_path =
ssl_key_path =
```

**新建文件**：`backend/routers/ws_config.py`

```python
@router.get("/api/ws/config")
async def get_ws_config():
    """公共无鉴权接口：返回当前WebSocket连接配置"""
    config = get_app_config()
    protocol = config.get('WEBSOCKET', 'protocol', fallback='ws')
    host = config.get('WEBSOCKET', 'host', fallback='localhost')
    port = config.get('WEBSOCKET', 'port', fallback='8001')
    return {
        "code": 200,
        "data": {
            "protocol": protocol,
            "host": host,
            "port": int(port),
            "url": f"{protocol}://{host}:{port}/ws/status/frontend/"
        }
    }

@router.post("/api/ws/config")
async def update_ws_config(request: WsConfigRequest, user: dict = Depends(get_current_user)):
    """管理员更新WebSocket协议配置（需管理员权限）"""
    # 1. 验证用户是否为管理员
    # 2. 更新config.ini中WEBSOCKET.protocol
    # 3. 通知所有在线用户协议变更
    # 4. 广播 protocol_changed 事件
    await status_manager.broadcast_all(
        status_manager.build_message(
            "protocol_changed",
            {"new_protocol": request.protocol}
        )
    )
```

**修改文件**：`backend/main.py`

- 注册 `ws_config` 路由
- startup时读取WEBSOCKET配置节

### 前端开发方案

**修改文件**：`src/utils/websocket.ts`

```typescript
// 移除硬编码协议推断，动态获取配置
async connect() {
  const config = await fetch('/api/ws/config').then(r => r.json())
  const wsUrl = config.data.url + this.clientId
  this.ws = new WebSocket(wsUrl)
}

// 处理协议变更事件
if (message.type === 'protocol_changed') {
  this.disconnect()
  this.connect()
}
```

***

## 9.9 F-08：连接状态增强（P2）

### 需求描述

连接状态可视化：连接中、已连接、断开、重连中、SSL异常、协议不匹配。分类捕获异常。

### 前端开发方案

**修改文件**：`src/utils/websocket.ts`

```typescript
export type WsConnectionState =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'ssl_error'
  | 'protocol_mismatch'

class WebSocketService {
  public connectionState = ref<WsConnectionState>('disconnected')

  // onopen
  this.connectionState.value = 'connected'

  // onclose 分类处理
  this.connectionState.value = 'disconnected'
  if (event.code === 4001) {
    // Token鉴权失败 → 不重连
    return
  }
  if (event.code === 1015) {
    this.connectionState.value = 'ssl_error'
  }

  // onerror 分类捕获
  // SSL握手失败 / 证书过期 / 域名拦截
}
```

**修改文件**：`src/components/Footer/src/Footer.vue`

```typescript
const stateLabel = computed(() => {
  const map: Record<WsConnectionState, string> = {
    connecting: '连接中...',
    connected: '已连接',
    disconnected: '未连接',
    reconnecting: '重连中...',
    ssl_error: 'SSL异常',
    protocol_mismatch: '协议不匹配'
  }
  return map[connectionState.value]
})

const stateColor = computed(() => {
  const map: Record<WsConnectionState, string> = {
    connecting: '#E6A23C',
    connected: '#67C23A',
    disconnected: '#F56C6C',
    reconnecting: '#E6A23C',
    ssl_error: '#F56C6C',
    protocol_mismatch: '#F56C6C'
  }
  return map[connectionState.value]
})
```

***

## 9.10 F-09：在线聊天系统（P3）

### 需求描述

一对一私聊、多人群聊。支持文字消息和文件传输。消息已读、未读统计。在线状态指示。会话列表实时同步。所有用户进入聊天时默认加入大厅房间，可在大厅发送并查看消息。

> **简化说明**：原需求包含表情包、图片、撤回、删除等功能，现简化为核心文字+文件传输，降低开发复杂度。表情包和图片可在后续版本按需增加。

### 默认大厅房间需求

所有用户在进入聊天系统时必须自动加入一个名为"大厅"的公共聊天房间，作为默认的公共交流空间。

**大厅房间规范**：

| 规范项 | 要求 | 说明 |
| ---- | ---- | ---- |
| 房间ID | `lobby` | 固定ID，全局唯一 |
| 房间名称 | 大厅 | 显示在会话列表中 |
| 房间类型 | `group` | 群聊类型 |
| 自动加入 | 用户首次获取会话列表时自动创建 | 后端 `getChatSessions` 接口自动检查并创建大厅会话 |
| 置顶显示 | 大厅在会话列表中始终排在第一位 | 排序规则：`CASE WHEN room_id = 'lobby' THEN 0 ELSE 1 END` |
| 默认选中 | 打开聊天窗口时默认选中大厅 | 前端 ChatWindow 组件 visible 变化时自动选中 lobby |
| 消息广播 | 大厅消息通过 WebSocket 广播给所有在线用户 | 与普通群聊消息机制一致 |

**实现方式**：

- 后端 `getChatSessions` 接口在返回会话列表前，先检查用户是否已有 `lobby` 会话记录，若没有则自动创建
- 前端 ChatWindow 组件在 `visible` 变为 `true` 时，检查 `currentRoomId` 是否为空，若为空则自动选中 `lobby`
- 大厅房间消息的发送、接收、未读计数与普通群聊完全一致

### 数据库设计

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    room_id VARCHAR(100) NOT NULL,
    sender_id INT NOT NULL,
    sender_name VARCHAR(100),
    content_type VARCHAR(20) NOT NULL DEFAULT 'text' COMMENT 'text/file',
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_room_created (room_id, created_at),
    INDEX idx_sender (sender_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    room_id VARCHAR(100) NOT NULL,
    last_message_id BIGINT DEFAULT NULL,
    unread_count INT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_room (user_id, room_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

> **简化说明**：移除了 `chat_message_status` 表（已读状态仅通过 `chat_sessions.unread_count` 追踪），减少表数量和复杂度。

### 后端开发方案

**新建文件**：`backend/routers/chat.py`

| 端点                            | 方法   | 功能                        |
| ----------------------------- | ---- | ------------------------- |
| `/api/chat/send`              | POST | 发送消息                      |
| `/api/chat/history/{room_id}` | GET  | 获取聊天历史                    |
| `/api/chat/read/{room_id}`    | POST | 标记房间消息已读（清零unread\_count） |
| `/api/chat/sessions`          | GET  | 获取会话列表                    |
| `/api/chat/upload`            | POST | 上传文件                      |

### 前端开发方案

#### 9.10.1 悬浮聊天图标组件

**新建文件**：`src/components/ChatFloatingIcon/index.vue`

全局悬浮聊天入口图标，在所有页面始终可见。

**功能要求**：

| 功能项  | 要求                           | 说明                                 |
| ---- | ---------------------------- | ---------------------------------- |
| 悬浮显示 | 始终悬浮在页面右下角（默认位置）             | `position: fixed`，`z-index` 高于页面内容 |
| 点击展开 | 点击图标 → 打开聊天窗口                | 聊天窗口从图标位置弹出                        |
| 点击缩小 | 聊天窗口打开时，点击图标或窗口内缩小按钮 → 收起为图标 | 窗口收起动画，回到图标状态                      |
| 拖拽移动 | 长按/鼠标拖拽图标可自由移动位置             | 拖拽结束后自动吸附到最近的屏幕边缘                  |
| 位置记忆 | 拖拽后的位置持久化到 `localStorage`    | 刷新页面后恢复到上次拖拽位置                     |
| 未读提示 | 图标右上角显示未读消息数红点/数字            | 实时更新，WebSocket驱动                   |
| 在线状态 | 图标颜色/光晕反映WebSocket连接状态       | 绿色=已连接，灰色=断开，黄色=重连中                |
| 自动隐藏 | 聊天窗口打开时图标自动隐藏                | 窗口关闭后图标重新显示                        |

**组件结构**：

```typescript
interface ChatFloatingIconProps {
  unreadCount: number
  connectionState: WsConnectionState
}

interface ChatFloatingIconEmits {
  (e: 'toggle-chat'): void
}

const isDragging = ref(false)
const position = reactive({ x: window.innerWidth - 80, y: window.innerHeight - 80 })
const dragStart = reactive({ x: 0, y: 0 })

const savedPos = localStorage.getItem('chat_icon_position')
if (savedPos) {
  const parsed = JSON.parse(savedPos)
  position.x = parsed.x
  position.y = parsed.y
}

const onMouseDown = (e: MouseEvent) => {
  isDragging.value = false
  dragStart.x = e.clientX - position.x
  dragStart.y = e.clientY - position.y
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const onMouseMove = (e: MouseEvent) => {
  isDragging.value = true
  position.x = e.clientX - dragStart.x
  position.y = e.clientY - dragStart.y
}

const onMouseUp = () => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)

  const edgeThreshold = 20
  if (position.x < edgeThreshold) position.x = 16
  if (position.x > window.innerWidth - 60 - edgeThreshold) position.x = window.innerWidth - 60
  if (position.y < edgeThreshold) position.y = 16
  if (position.y > window.innerHeight - 60 - edgeThreshold) position.y = window.innerHeight - 60

  localStorage.setItem('chat_icon_position', JSON.stringify({ x: position.x, y: position.y }))

  setTimeout(() => { isDragging.value = false }, 100)
}

const onClick = () => {
  if (!isDragging.value) {
    emit('toggle-chat')
  }
}
```

**样式规范**：

```css
.chat-floating-icon {
  position: fixed;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  cursor: grab;
  user-select: none;
  transition: box-shadow 0.3s, transform 0.2s;
  z-index: 9999;
}

.chat-floating-icon:active {
  cursor: grabbing;
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
}

.chat-floating-icon--connected {
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.4), 0 4px 12px rgba(0, 0, 0, 0.25);
}

.chat-floating-icon--disconnected {
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.4), 0 4px 12px rgba(0, 0, 0, 0.25);
}

.chat-floating-icon--reconnecting {
  box-shadow: 0 0 0 3px rgba(230, 162, 60, 0.4), 0 4px 12px rgba(0, 0, 0, 0.25);
}

.chat-floating-icon__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  border-radius: 9px;
  background: #F56C6C;
  color: #fff;
  font-size: 11px;
  text-align: center;
  padding: 0 4px;
}
```

#### 9.10.2 聊天窗口组件

**新建文件**：`src/components/ChatWindow/index.vue`

从悬浮图标弹出/收起的聊天主窗口。

**功能要求**：

| 功能项     | 要求                                    | 说明               |
| ------- | ------------------------------------- | ---------------- |
| 窗口定位    | 从悬浮图标位置弹出                             | 窗口右下角对齐图标位置      |
| 窗口尺寸    | 默认 380×520px                          | 可通过拖拽右下角调整大小     |
| 展开/收起动画 | `transform: scale()` + `opacity` 过渡动画 | 300ms ease-out   |
| 收起方式    | 点击悬浮图标 / 窗口内缩小按钮 / ESC键               | 三种方式均可收起         |
| 窗口层级    | `z-index: 9998`，低于悬浮图标                | 确保图标始终在最上层       |
| 移动端适配   | 窗口全屏展示                                | 屏幕宽度 < 768px 时全屏 |

**窗口布局**：

```
┌──────────────────────────────────┐
│  聊天  [—] [□] [×]              │  ← 标题栏（可拖拽移动窗口）
├──────────┬───────────────────────┤
│ 搜索     │  对方用户名  在线      │
│ ─────── │  ──────────────────  │
│ 会话1    │  消息气泡区域          │
│ 会话2    │                       │
│ 会话3    │                       │
│ ...      │                       │
│          │  ──────────────────  │
│          │  [附件] 输入框 [发送]  │
└──────────┴───────────────────────┘
  左侧会话列表        右侧聊天区域
```

#### 9.10.3 全局注册与状态管理

**修改文件**：`src/App.vue`

```typescript
import ChatFloatingIcon from '@/components/ChatFloatingIcon/index.vue'
import ChatWindow from '@/components/ChatWindow/index.vue'

const chatVisible = ref(false)
const unreadCount = ref(0)

const toggleChat = () => {
  chatVisible.value = !chatVisible.value
}

const { onMessage } = useWebSocket()
onMessage((msg) => {
  if (msg.type === 'chat_message' && !chatVisible.value) {
    unreadCount.value++
  }
})
```

```html
<template>
  <router-view />
  <ChatFloatingIcon
    :unread-count="unreadCount"
    :connection-state="connectionState"
    @toggle-chat="toggleChat"
  />
  <ChatWindow
    :visible="chatVisible"
    :position="iconPosition"
    @close="chatVisible = false"
  />
</template>
```

#### 9.10.4 聊天业务页面

**新建文件**：`src/views/SystemTools/Chat.vue`

完整聊天管理页面（从菜单进入），提供比悬浮窗口更完整的功能：会话管理、聊天记录搜索、群聊管理。

***

## 9.11 F-10：多人协同编辑（P3）

### 需求描述

基于现有行级锁+乐观锁机制，支持多用户同时编辑同一表格的不同行。行级编辑互不冲突，编辑者标识实时显示。

> **简化说明**：原需求包含CRDT/OT算法、字段级锁定、光标同步等，这些在100人内部系统中过度设计。现有F-02（行级锁）和F-01（乐观锁）已满足"不同用户编辑不同行互不冲突"的核心需求。字段级锁定和CRDT标记为远期可选扩展。

### 当前能力覆盖

| 需求            | 已有方案                          | 覆盖状态  |
| ------------- | ----------------------------- | ----- |
| 不同用户编辑不同行互不冲突 | F-02 行级锁                      | ✅ 已覆盖 |
| 同行编辑冲突检测与处理   | F-01 乐观锁                      | ✅ 已覆盖 |
| 编辑者标识实时显示     | F-04 协作广播 row\_locked         | ✅ 已覆盖 |
| 数据实时同步        | F-03 局部更新 + F-04 row\_updated | ✅ 已覆盖 |

### 远期可选扩展（不在当前开发计划内）

- **字段级锁定**：不同用户可同时编辑同一行的不同字段。需新增 `collab_field_locks` 表和字段级广播事件。
- **CRDT/OT算法**：支持同一字段的并发编辑自动合并。需集成Yjs或Automerge库，开发量巨大。
- **光标位置同步**：实时显示其他用户的光标位置。需高频WebSocket推送，对性能要求高。

***

## 9.12 F-11：系统实时通知与管控（P3）

### 需求描述

全站弹窗通知、站内消息推送。后端可主动下发指令，强制刷新前端权限、菜单。后台可实时踢出指定在线用户。

> **简化说明**：原需求包含审批流推送、通知已读状态追踪等，现简化为通知推送+踢人+强制刷新核心功能。已读状态追踪移出当前开发计划。

### 后端开发方案

**新建文件**：`backend/routers/notifications.py`

| 端点                                 | 方法   | 功能          |
| ---------------------------------- | ---- | ----------- |
| `/api/notifications/broadcast`     | POST | 全站广播通知      |
| `/api/notifications/send`          | POST | 发送给指定用户     |
| `/api/notifications/kick-user`     | POST | 踢出指定用户      |
| `/api/notifications/force-refresh` | POST | 强制刷新前端权限/菜单 |

### 数据库设计

```sql
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT 'system/approval/alert',
    title VARCHAR(200) NOT NULL,
    content TEXT,
    sender_id INT DEFAULT NULL,
    target_type VARCHAR(20) DEFAULT 'all' COMMENT 'all/user/role/department',
    target_ids JSON DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

> **简化说明**：移除了 `notification_status` 表（已读状态追踪），通知为即发即弃模式，简化实现。

### 前端开发方案

- 全局通知组件（右上角弹出）
- WebSocket接收 `system_notification` 事件类型
- 收到 `force_refresh` 事件时重新获取权限和菜单
- 收到 `kick_user` 事件时断开连接并跳转登录页

***

## 9.13 数据清理策略

### 需求描述

`row_versions` 和 `edit_history` 表会持续增长，需要定期清理机制，避免数据库膨胀。

### 清理规则

| 表               | 保留策略        | 清理方式                            |
| --------------- | ----------- | ------------------------------- |
| `row_versions`  | 随月度表归档时一并清理 | 月度表归档时，DELETE对应table\_name的版本记录 |
| `edit_history`  | 默认保留90天     | 后端启动时自动清理90天前的记录；提供手动清理API      |
| `notifications` | 默认保留30天     | 后端启动时自动清理30天前的记录                |

### 后端实现

**修改文件**：`backend/main.py`

```python
@app.on_event("startup")
async def cleanup_expired_data():
    """启动时清理过期数据"""
    # DELETE FROM edit_history WHERE created_at < NOW() - INTERVAL 90 DAY
    # DELETE FROM notifications WHERE created_at < NOW() - INTERVAL 30 DAY
```

**新增端点**：`POST /api/system/cleanup/`（管理员）

- 参数：`table_name`（可选）、`days`（可选，默认90）
- 手动触发数据清理

***

## 9.14 广播失败处理

### 策略

更新操作以数据库写入为准，广播失败仅记录日志，不影响业务结果。

### 实现方式

```python
async def broadcast_to_room(self, room_id: str, message: dict):
    if room_id not in self.rooms:
        return
    msg_str = json.dumps(message)
    for client_id in list(self.rooms[room_id]["members"].keys()):
        conn = self._find_connection(client_id)
        if conn:
            try:
                await conn["websocket"].send_text(msg_str)
            except Exception as e:
                logger.warning(f"广播失败 room={room_id} client={client_id}: {e}")
                continue
```

### 用户端补偿

- 收到 `row_updated` 事件时调用 `getSingleRow` 获取最新数据
- 断线重连后主动调用 `getActiveLocks` 和刷新当前表格数据
- 不依赖广播的可靠传递，业务层始终可自行恢复

***

## 9.15 并发模型

### 问题

`collaboration_service.py` 使用 `async def` 但内部调用同步MySQL操作（`get_db_connection`），会阻塞事件循环。

### 解决方案

使用 `asyncio.to_thread` 包装同步数据库调用：

```python
import asyncio

async def get_or_create_version(table_name: str, row_id: str) -> dict:
    """获取行版本号（异步包装）"""
    return await asyncio.to_thread(_get_or_create_version_sync, table_name, row_id)

def _get_or_create_version_sync(table_name: str, row_id: str) -> dict:
    """同步数据库操作"""
    config = get_app_config()
    with get_db_connection("USER_DB", config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT version, updated_by, updated_at FROM row_versions WHERE table_name=%s AND row_id=%s",
                (table_name, row_id)
            )
            result = cursor.fetchone()
            if result:
                return {"version": result[0], "updated_by": result[1], "updated_at": str(result[2])}
            cursor.execute(
                "INSERT INTO row_versions (table_name, row_id, version) VALUES (%s, %s, 1)",
                (table_name, row_id)
            )
            conn.commit()
            return {"version": 1, "updated_by": None, "updated_at": None}
```

### 内存锁操作

F-02的行级锁使用内存字典，操作为纯CPU计算，无需异步包装，直接在事件循环中执行即可。

***

## 9.16 测试策略

### 每阶段测试要求

| 阶段  | 测试内容                          | 验收标准                                                      |
| --- | ----------------------------- | --------------------------------------------------------- |
| 阶段1 | 乐观锁冲突检测、行级锁加锁/解锁/过期、局部更新、协作广播 | 多用户同时编辑不同行无冲突；同行编辑弹出冲突对话框；锁5分钟自动过期                        |
| 阶段2 | 编辑历史记录、消息格式校验、房间隔离            | 历史记录完整记录变更字段；所有消息包含fromUserId/roomId/timestamp；不同房间消息互不干扰 |
| 阶段3 | Token鉴权、双协议切换、连接状态            | 无Token连接被拒绝；切换协议后客户端自动重连；6种连接状态正确显示                       |
| 阶段4 | 聊天收发、通知推送、踢人                  | 文字和文件消息正常收发；通知弹窗正确显示；被踢用户自动断开                             |

### 测试方式

- 手动多浏览器窗口测试（模拟多用户）
- 后端单元测试（锁逻辑、版本逻辑）
- 集成测试（WebSocket连接→协作事件→前端更新完整链路）

***

## 9.17 回滚方案

### 版本管理

每个阶段独立版本号，部署失败可回滚到上一版本。

| 阶段  | 版本号     | 说明                   |
| --- | ------- | -------------------- |
| 阶段1 | v2.11.0 | 乐观锁+协作锁+局部更新+广播      |
| 阶段2 | v2.12.0 | 编辑历史+消息格式+房间+Token鉴权 |
| 阶段3 | v2.13.0 | 双协议+连接状态增强           |
| 阶段4 | v2.14.0 | 聊天+通知                |

### 回滚步骤

1. 停止后端服务
2. 恢复上一版本的部署包
3. 执行数据库回滚SQL（如需）
4. 重启服务
5. 验证功能正常

### 数据库变更回滚

每个阶段的数据库变更需提供对应的回滚SQL：

```sql
-- 阶段1回滚
DROP TABLE IF EXISTS row_versions;
DROP TABLE IF EXISTS edit_history;
```

***

# 10. 分阶段实施计划

## 10.1 阶段划分

| 阶段  | 优先级 | 包含功能                      | 目标                    |
| --- | --- | ------------------------- | --------------------- |
| 阶段1 | P0  | F-01 + F-02 + F-03 + F-04 | 乐观锁+协作锁+局部更新+协作广播完整闭环 |
| 阶段2 | P1  | F-05 + F-06               | 编辑历史+Token鉴权          |
| 阶段3 | P2  | F-07 + F-08               | 双协议配置+连接状态增强          |
| 阶段4 | P3  | F-09 + F-10 + F-11        | 在线聊天+协同编辑+系统通知        |

## 10.2 阶段1详细任务清单（P0）

| 序号  | 任务          | 修改文件                                        | 操作                                                                          |
| --- | ----------- | ------------------------------------------- | --------------------------------------------------------------------------- |
| 1.1 | 建表逻辑        | `backend/main.py`                           | 修改：startup中自动创建row\_versions表                                               |
| 1.2 | Pydantic模型  | `backend/core/models.py`                    | 修改：新增LockRequest/UnlockRequest，UpdateMatchRequest增加version/force\_overwrite |
| 1.3 | 协作服务        | `backend/services/collaboration_service.py` | 新建：版本管理+锁管理（内存）                                                             |
| 1.4 | 后端API       | `backend/routers/split_match.py`            | 修改：新增lock/unlock/active-locks/row-version端点，修改update端点                      |
| 1.5 | WebSocket广播 | `backend/core/websocket_manager.py`         | 修改：新增build\_message+房间管理+broadcast\_to\_room                                |
| 1.6 | WebSocket端点 | `backend/routers/websocket_endpoints.py`    | 修改：新增协作房间加入/离开/消息路由                                                         |
| 1.7 | 前端WebSocket | `src/utils/websocket.ts`                    | 修改：新增协作回调、房间管理、WsMessage接口对齐                                                |
| 1.8 | 前端API       | `src/api/split-match/index.ts`              | 修改：新增lockRow/unlockRow/getActiveLocks/getRowVersion/getSingleRow            |
| 1.9 | 前端组件        | `src/views/SystemTools/SplitMatch.vue`      | 修改：行级标记+锁检测+冲突处理+局部更新                                                       |

## 10.3 阶段2详细任务清单（P1）

| 序号  | 任务        | 修改文件                                        | 操作                                              |
| --- | --------- | ------------------------------------------- | ----------------------------------------------- |
| 2.1 | 编辑历史建表    | `backend/main.py`                           | 修改：startup中创建edit\_history表                     |
| 2.2 | 编辑历史服务    | `backend/services/collaboration_service.py` | 修改：新增record\_edit\_history/get\_edit\_history   |
| 2.3 | 编辑历史API   | `backend/routers/split_match.py`            | 修改：新增edit-history端点，update端点增加changed\_fields记录 |
| 2.4 | 编辑历史UI    | `src/views/SystemTools/SplitMatch.vue`      | 修改：新增编辑历史抽屉/对话框                                 |
| 2.5 | Token鉴权   | `backend/routers/websocket_endpoints.py`    | 修改：WebSocket端点增加Token验证                         |
| 2.6 | 前端Token传递 | `src/utils/websocket.ts`                    | 修改：连接URL携带Token                                 |

## 10.4 阶段3详细任务清单（P2）

| 序号  | 任务     | 修改文件                                   | 操作                         |
| --- | ------ | -------------------------------------- | -------------------------- |
| 3.1 | 双协议配置  | `backend/config.ini`                   | 修改：新增\[WEBSOCKET]节         |
| 3.2 | 配置接口   | `backend/routers/ws_config.py`         | 新建：GET/POST /api/ws/config |
| 3.3 | 前端动态获取 | `src/utils/websocket.ts`               | 修改：connect方法动态获取配置         |
| 3.4 | 连接状态增强 | `src/utils/websocket.ts`               | 修改：6种状态枚举+分类异常捕获           |
| 3.5 | 状态可视化  | `src/components/Footer/src/Footer.vue` | 修改：显示6种连接状态                |

## 10.5 阶段4详细任务清单（P3）

| 序号  | 任务     | 修改文件                                        | 操作                                          |
| --- | ------ | ------------------------------------------- | ------------------------------------------- |
| 4.1 | 聊天数据库  | `backend/main.py`                           | 修改：startup中创建chat\_messages+chat\_sessions表 |
| 4.2 | 聊天后端   | `backend/routers/chat.py`                   | 新建：聊天API端点                                  |
| 4.3 | 悬浮聊天图标 | `src/components/ChatFloatingIcon/index.vue` | 新建：悬浮图标组件                                   |
| 4.4 | 聊天窗口   | `src/components/ChatWindow/index.vue`       | 新建：弹出式聊天窗口组件                                |
| 4.5 | 全局注册   | `src/App.vue`                               | 修改：注册悬浮图标和聊天窗口                              |
| 4.6 | 聊天业务页面 | `src/views/SystemTools/Chat.vue`            | 新建：完整聊天管理页面                                 |
| 4.7 | 通知数据库  | `backend/main.py`                           | 修改：startup中创建notifications表                 |
| 4.8 | 通知后端   | `backend/routers/notifications.py`          | 新建：通知API端点                                  |
| 4.9 | 通知前端   | `src/components/NotificationCenter.vue`     | 新建：全局通知组件                                   |

***

# 11. 关键设计决策

| 决策项     | 选择                       | 理由                                           |
| ------- | ------------------------ | -------------------------------------------- |
| 版本存储    | 独立 `row_versions` 表      | 不修改月度表结构，零侵入，自动扩展                            |
| 锁存储     | 内存字典                     | 纯CPU操作无IO，服务重启锁自动清除，用户重新编辑即可重新加锁             |
| 锁过期     | 5分钟                      | 平衡安全性与用户体验                                   |
| 版本初始化   | 懒初始化                     | 首次编辑时才创建版本记录，节省空间                            |
| 协作广播    | 按表房间隔离                   | 不同月度表的编辑互不干扰                                 |
| 冲突处理    | 三选一（强制覆盖/放弃/重新编辑）        | 灵活应对不同场景                                     |
| 导入覆盖    | 管理员强制覆盖+自动解锁             | 符合需求"导入操作允许管理员强制覆盖"                          |
| 局部更新    | 单行数据请求+原地替换              | 符合文档"禁止整页刷新"要求                               |
| 消息格式    | 对齐文档3.4节统一格式             | 确保所有消息包含fromUserId/toUserId/roomId/timestamp |
| 房间命名    | 按类型前缀+业务ID               | 便于区分房间类型和路由消息                                |
| 双协议     | 后端配置驱动+前端动态获取            | 符合文档"禁止前端硬编码协议"要求                            |
| Token鉴权 | WebSocket URL查询参数传递      | 兼容浏览器WebSocket API（不支持自定义Header）             |
| 广播失败    | 仅记录日志不影响业务               | 更新操作以数据库写入为准，用户端可自行补偿恢复                      |
| 并发模型    | asyncio.to\_thread包装同步DB | 避免同步MySQL操作阻塞事件循环                            |
| 数据清理    | 启动时自动清理+手动API            | edit\_history保留90天，notifications保留30天        |

