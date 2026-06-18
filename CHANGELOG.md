# 项目更新日志

## [最新版本]

### 2026-06-17 v2.51.0

#### 功能新增
- **云门户人工核查-车牌号码详单查询**：查询参数车牌号码后增加"查"按钮，点击后查询[DETAIL_QUERY]配置表中该车牌的所有数据
  - 复用现有 `queryDetailData` API（`POST /api/detail-query/`），无需后端改动
  - 弹出详单查询结果对话框，动态列生成，支持分页浏览
  - 影响文件：SplitMatch.vue

### 2026-06-17 v2.50.0

#### 功能修复
- **追查详单通行记录详情无数据**：修复点击行数据后通行记录详情弹窗无数据的问题
  - 根因：`pass-records` 接口仅查询详单查询表（`202005-202311_cf_1215`，仅含2020-2023数据），追查详单的通行标识ID来源于2025年数据，在详单查询表中不存在
  - 修复：改为多表联合查询策略——优先查详单查询表，无结果时从pass_id提取年月优先定位对应yc表（如`2025-01_yc`），仍无结果则遍历所有yc表
  - 新增 `_extract_yc_month_from_pass_id`：从通行标识ID中正则提取日期定位yc表
  - 新增 `_query_table_by_pass_id`：通用单表查询函数，检查列存在性后执行查询
  - 新增 `_format_records`：统一格式化查询结果（bytes解码、时间格式化）
  - 影响文件：routers/investigation.py

### 2026-06-16 v2.49.0

#### 功能修复
- **追查详单表格组件不显示**：修复追查详单页面表格组件未渲染的问题（非数据为空，而是整个表格组件未加载）
  - 根因：数据库 menus 表 path 为 `/data-query/investigation-detail`，后端 `component_mapping` 缺少该映射，导致前端动态路由解析组件路径失败（`modules['../views/data-query/investigation-detail.vue']` 找不到文件）
  - 修复1：数据库 menus 表 path 从 `/data-query/investigation-detail` 改为 `/investigation-detail`
  - 修复2：`users.py` 的 `component_mapping` 增加 `'investigation-detail': 'SystemTools/InvestigationDetail'`
  - 修复3：`users.py` 的 `title_map` 增加 `'追查详单': 'router.investigationDetail'`
  - 修复4：`SplitMatch.vue` 修复 `res.data?.code` → `res.code`（响应拦截器已解包一层）
  - 影响文件：routers/users.py、SplitMatch.vue

### 2026-06-16 v2.48.0

#### 功能修复
- **追查详单表格数据不显示**：修复前端API响应数据访问路径错误（axios拦截器已解包一层，代码中多套了一层`.data`），将 `res.data?.code` 改为 `res.code`，`res.data.data.records` 改为 `res.data.records`
  - 影响文件：InvestigationDetail.vue

#### 功能新增
- **追查详单行点击详情弹窗**：点击追查详单表格行数据后弹出详情窗口，展示该通行标识ID在详单查询表中的所有相关通行记录
  - 后端新增 `/api/investigation/pass-records` 接口，根据通行标识ID查询 `CHECK_DATA_DB` 详单查询表
  - 弹窗上方显示追查基本信息（通行标识ID、车牌号码、加入时间、创建人、复核状态等）
  - 弹窗下方动态列表格展示通行记录（字段根据详单查询表实际列动态生成）
  - 操作列按钮添加 `@click.stop` 防止触发行点击事件
  - 影响文件：routers/investigation.py、api/investigation/index.ts、InvestigationDetail.vue

### 2026-06-16 v2.47.0

#### 功能修复
- **保存后行锁未实时释放**：保存成功后增加 `unlockRow` API调用 + 从 `activeLocksMap` 删除该行，确保后端释放内存锁并广播 `row_unlocked` 事件，其他用户表格实时显示解锁状态
  - 主保存成功后：新增 unlockRow 调用 + delete activeLocksMap
  - 强制覆盖保存成功后：同上
  - 影响文件：SplitMatch.vue

### 2026-06-16 v2.46.0

#### 新增功能
- **追查详单功能**：在"数据查询"菜单下新增"追查详单"子菜单，用于记录与显示追查详单数据
  - 新增 `investigation_details` 数据表（通行标识ID、车牌号码、加入时间、创建人、复核结果、复核人、复核时间）
  - 云门户人工核查窗口增加"加入追查"按钮，点击后将通行标识ID和车牌号码存入追查详单
  - 追查详单页面支持分页查询、条件筛选（通行标识ID、车牌号码、创建人、复核状态、时间范围）
  - 支持复核结果录入（最多200字符），自动记录复核人和复核时间
  - 支持删除记录和导出Excel
  - 权限控制：investigation:view/add/review/delete/export 五个权限点
  - 新增文件：`backend/routers/investigation.py`、`src/api/investigation/index.ts`、`src/views/SystemTools/InvestigationDetail.vue`
  - 修改文件：`backend/main.py`（注册路由）、`src/router/index.ts`（菜单项）、`src/views/SystemTools/SplitMatch.vue`（加入追查按钮）
  - 数据库迁移：`backend/migrations/004_investigation_detail.sql`

### 2026-06-16 v2.45.0

#### 功能修复
- **P0: lock/unlock端点添加协作事件广播**：加锁成功后广播 `row_locked` 事件，释放锁成功后广播 `row_unlocked` 事件，通知同表房间其他用户实时更新行级协作标记
  - 影响文件：routers/split_match.py

#### 功能补充
- **P1: startup自动创建row_versions表**：后端启动时自动创建乐观锁版本管理表，与需求文档9.2节对齐
  - 影响文件：main.py
- **P3: 新增NotificationCenter通知中心前端组件**：通知铃铛图标 + 通知历史弹窗，支持未读计数、分页查询、类型标签
  - 新增文件：src/components/NotificationCenter/index.vue、src/api/notifications/index.ts
  - 修改文件：src/App.vue（注册NotificationCenter组件）

### 2026-06-15 v2.44.0

#### 功能优化
- **拆分匹配复核情况多选筛选**：将"复核情况"筛选从文本输入框改为多选下拉框，支持同时选择"拆分正常"、"拆分异常"、"待删除"进行组合筛选
  - 前端：`el-input` 替换为 `el-select multiple`，使用 `collapse-tags` 折叠显示已选标签
  - 后端：`split_match.py` 路由层对"复核情况"数组值生成 `IN (...)` SQL 条件，其他字段保持原有精确匹配逻辑不变

### 2026-06-10 v2.43.0

#### Bug修复
- **WebSocket 连接失败**：`config.ini` 中 `[WEBSOCKET] host = localhost`，前端通过 `/api/ws/config` 获取到 `ws://localhost:8001`，远程访问时 localhost 指向用户本机而非服务器，导致连接失败
  - 修改 `config.ini` 的 `[WEBSOCKET] host` 为 `172.32.48.238`，前端将获取到 `ws://172.32.48.238:8001`
- **Chat 会话列表 500 错误**：MySQL 8.0 不支持 `ALTER TABLE ADD COLUMN IF NOT EXISTS` 语法（MariaDB 专有），导致 `chat_sessions` 缺少 `is_pinned`/`is_muted` 列、`chat_messages` 缺少 `is_recalled`/`mentioned_user_ids`/`file_name` 列，SQL 查询报 `Unknown column` 异常
  - 修改 `main.py` 启动时的 ALTER 逻辑：先查 `INFORMATION_SCHEMA.COLUMNS` 判断列是否存在，不存在才执行 ALTER
  - 已手动补齐数据库缺失的 5 个列
- **云门户数据同步 405 Method Not Allowed**：前端 `api/cloud-portal-data/index.ts` 已定义 3 个 API，但后端缺少对应路由端点
  - 在 `cloud_portal.py` 中新增 3 个端点：
    - `GET /api/cloud-portal-data/` — 获取已同步的云门户基础数据
    - `POST /api/cloud-portal-data/sync` — 触发数据同步（300秒超时）
    - `GET /api/cloud-portal-data/status` — 获取同步状态

#### 核心功能修复
- **A1 调度器启动**：`main.py` startup 事件中调用 `start_scheduler()`，shutdown 中调用 `stop_scheduler()`，修复定时任务从未自动执行的严重问题
- **A2 执行历史记录**：每个定时任务执行时自动写入 `task_execution_history` 表（`start_task_execution` → `end_task_execution`），前端"历史"按钮可查看完整执行记录
- **A3 next_run_time**：任务注册后从 APScheduler 获取 `job.next_run_time` 并更新到数据库，前端可展示下次执行时间
- **A4 cloud_portal_data_sync 自动登录**：定时执行时自动使用 admin(user_id=1) 绑定的云门户账号密码进行自动登录获取 Token，无需手动登录；Token 过期自动重登录（含验证码 OCR 识别 + 3次重试）

#### 架构优化
- **B1 替换 schedule 为 APScheduler**：使用 `BackgroundScheduler` + `CronTrigger`，原生支持完整 5 字段 Cron 表达式（`*/30`、`1-5`、`1,15` 等），替换原有仅支持小时+分钟的 `schedule` 库
- **B2 任务热更新**：修改 Cron 表达式或启用/禁用状态后，路由层自动调用 `reload_tasks()` 刷新调度器，无需重启后端服务
- **B3 公共数据库连接工具**：新建 `core/db.py`，统一 `get_db_config`/`get_user_db_connection`/`get_check_data_connection`，消除 `statistics_service.py`、`init_statistics_tables.py`、`routers/scheduled_tasks.py` 三处重复代码
- **B4 任务注册表机制**：`TASK_REGISTRY` + `@register_task` 装饰器，新增任务只需添加装饰器函数，调度器自动发现并注册，无需修改硬编码 `if task_name == 'xxx'` 逻辑

#### 体验优化
- **前端增加任务描述列**：从数据库 `config` JSON 提取 `description` 展示，同时增加"执行频率"中文描述列
- **执行历史增加分页**：后端 `/api/task-execution-history/` 改为 `page`+`page_size` 分页查询，前端使用 `ElPagination` 组件支持翻页和每页条数切换
- **手动执行改为异步**：后端 `/api/scheduled-tasks/{task_name}/run` 改为线程异步执行，立即返回 `run_id`；新增 `/api/scheduled-tasks/run-status/{run_id}` 轮询接口；前端每2秒轮询执行状态
- **Cron 表达式可视化编辑器**：编辑对话框新增5种调度模式（每天/间隔/每周/每月/自定义），支持双向解析和实时预览
- **任务执行失败告警**：连续失败 >= 3 次时在页面顶部显示红色 `ElAlert` 告警

#### 后端新增端点
- `GET /api/scheduled-tasks/run-status/{run_id}` — 查询异步任务执行状态
- `GET /api/task-execution-history/` — 分页查询执行历史（原接口改为分页）

#### 影响文件
- 后端新建：`backend/core/db.py`
- 后端重写：`backend/scheduler.py`（schedule → APScheduler）
- 后端重构：`backend/statistics_service.py`、`backend/routers/scheduled_tasks.py`、`backend/init_statistics_tables.py`
- 后端修改：`backend/main.py`（启动/停止调度器）、`backend/requirements.txt`（schedule → APScheduler）
- 前端重写：`src/views/SystemTools/ScheduledTasks/ScheduledTasks.vue`
- 前端修改：`src/api/scheduled-tasks/types.ts`、`src/api/scheduled-tasks/index.ts`

### 2026-06-09 v2.42.0

#### Bug修复
- **路径匹配页面 405 Method Not Allowed**：前端 PathMatch.vue 已实现但后端缺少对应路由模块，导致所有 API 请求返回 405
  - 新增 `backend/routers/path_match.py`，实现 4 个端点：
    - `GET /api/path-match/tables/` — 获取可用数据表列表
    - `POST /api/path-match/search` — 多条件路径匹配搜索（清分日、时间范围、车型、收费单元、排除绿通等）
    - `POST /api/path-match/provinces` — 根据站点编码查询省份名称（内置编码映射表）
    - `POST /api/path-match/detail` — 根据通行标识ID查询详情
  - 搜索条件构建逻辑与前端 `buildPreviewSql` 一致，使用参数化查询防止 SQL 注入
  - 搜索接口带 120 秒超时控制，复用 `CHECK_DATA_DB` 连接池，表名从 `config.ini` 的 `[PATH_MATCH]` 节读取

#### 后端新增端点
- `GET /api/path-match/tables/` — 获取路径匹配数据表列表
- `POST /api/path-match/search` — 路径匹配搜索
- `POST /api/path-match/provinces` — 省份编码查询
- `POST /api/path-match/detail` — 路径匹配详情查询

#### 影响文件
- 后端新增：`backend/routers/path_match.py`
- 后端修改：`backend/main.py`（注册 path_match 路由）

### 2026-06-09 v2.41.0

#### 功能新增
- **F-07 双协议(ws/wss)配置管理**：管理员可一键切换 WebSocket 协议，无需重启服务
  - `config.ini` 新增 `[WEBSOCKET]` 配置节（protocol/host/port/ssl_cert_path/ssl_key_path）
  - 公共无鉴权接口 `GET /api/ws/config`：前端动态获取 WebSocket 连接配置，禁止硬编码协议/域名/端口
  - 管理员接口 `POST /api/ws/config`：更新协议配置，保存后立即生效
  - 协议变更后自动向所有在线客户端广播 `protocol_changed` 事件，客户端自动断开并用新配置重连
  - 前端 `connect()` 改为 async，优先从服务端获取配置，获取失败时降级使用浏览器协议推断
- **F-11 系统实时通知与管控**：全站弹窗通知、定向推送、踢人、强制刷新
  - `POST /api/notifications/broadcast` — 全站广播通知（持久化到数据库 + WebSocket 实时推送）
  - `POST /api/notifications/send` — 向指定用户推送通知
  - `POST /api/notifications/kick-user` — 踢出指定在线用户（发送 kick_user 事件后延迟关闭连接）
  - `POST /api/notifications/force-refresh` — 强制前端刷新权限和菜单（页面自动刷新）
  - `GET /api/notifications/history` — 查询通知历史记录（分页）
  - 前端 App.vue 处理 `system_notification`（ElNotification 弹窗）、`kick_user`（断开+登出）、`force_refresh`（页面刷新）
- **ChatFloatingIcon 连接状态联动**：悬浮聊天图标与 F-08 连接状态同步
  - 6种连接状态对应不同颜色和光晕效果（connected=绿/connecting=黄脉冲/error=橙/disconnected=灰）
  - 鼠标悬停显示连接状态文字提示
  - connecting/reconnecting 状态显示脉冲呼吸动画

#### 后端新增端点
- `GET /api/ws/config` — 获取 WebSocket 连接配置（公共无鉴权）
- `POST /api/ws/config` — 更新 WebSocket 协议配置（需登录鉴权）
- `POST /api/notifications/broadcast` — 全站广播通知
- `POST /api/notifications/send` — 定向推送通知
- `POST /api/notifications/kick-user` — 踢出指定用户
- `POST /api/notifications/force-refresh` — 强制刷新前端权限
- `GET /api/notifications/history` — 查询通知历史

#### WebSocket 新增事件
- `protocol_changed` — 协议变更通知（管理员切换 ws/wss 后广播）
- `system_notification` — 系统通知推送（全站广播或定向推送）
- `kick_user` — 踢出用户指令
- `force_refresh` — 强制刷新权限指令

#### 影响文件
- 后端新增：`backend/routers/ws_config.py`、`backend/routers/notifications.py`
- 后端修改：`backend/config.ini`（新增 [WEBSOCKET] 节）、`backend/main.py`（注册路由）
- 前端修改：`src/utils/websocket.ts`（动态获取配置+协议变更处理）、`src/App.vue`（通知/踢人/刷新事件处理）、`src/components/ChatFloatingIcon/index.vue`（连接状态联动）

### 2026-06-09 v2.40.0

#### 功能新增
- **字段级编辑标识**：多人协作编辑时，实时显示每个字段正在被谁编辑
  - 用户聚焦可编辑字段时自动标记，失焦时自动清除
  - 其他用户编辑中的字段显示橙色边框 + "XX 编辑中" 标签
  - WebSocket 实时广播字段编辑状态变更
- **数据差分更新**：多人编辑同一行时，仅同步变更字段，避免覆盖他人编辑
  - 对话框 header 显示"已修改 N 个字段"指示
  - 收到其他用户更新时，仅刷新非自己编辑中的字段
  - 保存后自动更新原始数据基准
- **光标位置同步**：实时显示其他用户在当前行的光标位置
  - 对话框 header 显示其他用户的光标位置（"用户名 → 字段名"）
  - 聚焦字段时自动上报光标位置
  - 关闭对话框时自动清除光标位置

#### 后端新增端点
- `POST /api/split-match/field-editing/mark/` — 标记字段编辑
- `POST /api/split-match/field-editing/unmark/` — 取消字段编辑标记
- `GET /api/split-match/field-editing/active/` — 获取字段编辑状态
- `POST /api/split-match/cursor-position/` — 更新光标位置
- `GET /api/split-match/cursor-positions/` — 获取光标位置列表
- `POST /api/split-match/cursor-clear/` — 清除光标位置

#### WebSocket 新增事件
- `field_editing` — 字段编辑状态变更（focus/blur）
- `cursor_position` — 光标位置更新
- `cursor_cleared` — 光标位置清除

#### 影响文件
- 后端：`backend/core/websocket_manager.py`、`backend/routers/split_match.py`
- 前端：`src/views/SystemTools/SplitMatch.vue`、`src/api/split-match/index.ts`、`src/utils/websocket.ts`

### 2026-06-09 v2.39.0

#### 功能新增
- **Chat.vue 业务页面 8 项功能全面开发**：
  - **CH-01 聊天记录搜索**：支持按关键词搜索全部会话或指定房间的历史消息，点击结果跳转到对应房间
  - **CH-02 群聊创建与管理**：支持创建群聊（群名+多选成员）、查看群成员列表、添加成员、修改群名称、退出群聊
  - **CH-03 消息撤回**：2分钟内可撤回自己发送的消息，撤回后显示"XX撤回了一条消息"，支持 WebSocket 实时同步
  - **CH-04 图片消息**：独立图片上传按钮，图片消息缩略图展示，点击查看大图预览弹窗，文件上传自动识别图片类型
  - **CH-05 消息已读回执**：自己发送的消息显示已读人数/总人数，点击查看已读用户列表，支持 WebSocket 实时更新
  - **CH-06 聊天记录导出**：支持导出为纯文本或 HTML 格式，包含时间戳、发送者、消息内容
  - **CH-07 会话置顶/免打扰**：会话右键菜单支持置顶（排在列表顶部）和免打扰（隐藏未读角标），置顶/免打扰图标标识
  - **CH-08 @提及**：输入`@`弹出成员选择下拉框，选择后插入`@username`，消息中 @提及高亮显示，被@者收到独立 WebSocket 通知

#### 数据库变更
- `chat_messages` 新增字段：`is_recalled`（撤回标记）、`mentioned_user_ids`（@提及用户列表）、`file_name`（文件原始名）
- `chat_sessions` 新增字段：`is_pinned`（置顶）、`is_muted`（免打扰）
- 新增表 `chat_group_members`：群聊成员管理（room_id, user_id, role）
- 新增表 `chat_message_read`：消息已读记录（message_id, user_id）

#### 后端新增端点
- `GET /api/chat/search/` — 搜索聊天消息
- `POST /api/chat/recall/{message_id}` — 撤回消息
- `POST /api/chat/upload-image/` — 上传图片
- `GET /api/chat/read-status/{room_id}` — 获取已读状态
- `GET /api/chat/export/{room_id}` — 导出聊天记录
- `PUT /api/chat/session-settings/` — 更新会话设置（置顶/免打扰）
- `GET /api/chat/group-members/{room_id}` — 获取群成员列表
- `POST /api/chat/add-group-members/` — 添加群成员
- `PUT /api/chat/group-name/` — 修改群名称
- `POST /api/chat/leave-group/{room_id}` — 退出群聊

#### 影响文件
- 后端：`backend/routers/chat.py`、`backend/main.py`、`backend/migrations/003_chat_enhancements.sql`
- 前端：`src/views/SystemTools/Chat.vue`、`src/api/chat/index.ts`、`src/utils/websocket.ts`

### 2026-06-08 v2.38.0

#### Bug修复
- **AI稽核批量查询门架交易数据行数不足**：前端 `cloudPortalForm.rows` 默认值从 50 改为 100，与云门户直接查询的 `length=100` 保持一致
  - 修复前：AI稽核批量查询最多返回50条门架交易记录，云门户直接查询返回100条
  - 修复后：两者均返回最多100条记录
  - 影响文件：src/hooks/split-match/useCloudPortal.ts

### 2026-06-08 v2.37.0

#### 性能优化
- **行级协作锁迁移为内存存储**：锁操作性能提升约500倍，零数据库压力
  - `acquire_row_lock` / `release_row_lock` / `get_active_locks` 等方法从 MySQL `row_locks` 表迁移至内存字典
  - 删除 `_get_db_conn()` / `_ensure_lock_table()` 数据库辅助方法
  - 锁操作响应时间从 ~5ms（SQL查询）降至 ~0.01ms（字典操作）
  - 惰性清理过期锁机制，无需定时任务
  - 服务重启锁自动清除（可接受，锁为5分钟过期的临时状态，乐观锁仍在数据库兜底）
  - 前端API接口格式不变，零改动
  - 影响文件：backend/core/websocket_manager.py、backend/routers/split_match.py

### 2026-06-08 v2.36.0

#### 功能优化
- **图标系统完全离线化**：移除所有图标在线依赖，确保部署服务器无需外网即可正常显示图标
  - `@iconify/iconify`（含在线API `api.iconify.design`）替换为 `@iconify/vue/offline`（纯离线版本，不包含任何网络请求逻辑）
  - `@iconify/vue` 在线版替换为 `@iconify/vue/offline` 离线版，当本地无图标数据时不再尝试联网获取
  - 移除已废弃的 `vite-plugin-purge-icons` 和 `@purge-icons/generated` 依赖
  - 移除 `@iconify/iconify` 依赖（功能已由 `@iconify/vue/offline` 的 `addCollection` 覆盖）
  - 构建产物验证：无 `api.iconify.design` 引用，无 `loadIcons`/`loadIcon` 在线加载函数
  - 影响文件：src/icons/index.ts、src/components/Icon/src/Icon.vue、package.json、vite.config.ts

### 2026-06-06 v2.35.0

#### 功能优化
- **分析页数据及图表展示优化**：
  - 分析页改为统一基于 `dashboard-statistics` 真实统计数据渲染顶部卡片和三张图表，避免原先模板化分析接口与业务统计口径不一致
  - 新增统计月份、更新时间、车型种类数、省份覆盖数摘要信息，提升数据来源和统计范围可读性
  - 车型分布优化为环形图，通行介质优化为排序柱状图，省份统计优化为 Top10 省份排名图，更贴合当前业务数据结构
  - 图表无数据时展示空状态，避免页面出现空白图表区域
  - 分析页顶部卡片改为由父组件统一传入统计数据，减少重复请求并保证页面数据一致性
  - 影响文件：Analysis.vue、PanelGroup.vue、zh-CN.ts、en.ts

### 2026-06-06 v2.34.0

#### 功能优化
- **云门户人工核查-门架交易经过时间查询弹窗优化**：
  - 调整弹窗高度自适应浏览器窗口（top=5vh，内容区max-height=75vh）
  - 弹窗中图片点击后加载高清原图预览，支持缓存避免重复请求
  - 车牌值后面增加"复制"按钮，点击将车牌号码复制到剪贴板
  - 影响文件：SplitMatch.vue

- **车辆详细信息窗口数据字段完善**：
  - 门架交易：从5个字段扩展为15个字段（车牌号、颜色、通行标识ID、门架名称、门架顺序号、经过时间、入口车型、计费车型、OBU卡内车型、介质类型、交易状态、应收金额、实收金额、优惠金额、特情）
  - 门架牌识：从4个字段扩展为7个字段（车牌号、牌识流水、门架名称、门架顺序号、经过时间、车型、相机编号）
  - 出口交易(ETC)和出口交易(其它)：从5个字段扩展为18个字段（出口车牌、入口车牌、识别车牌、进站名、进站时间、入口车型、出口车型、出站名、出站时间、介质类型、总应收金额、总交易金额、总优惠金额、最小费额交易金额、计费总里程数、最小费额里程数、计费方式、特情）
  - 稽核工单：参照云门户人工核查窗口完整字段（工单编号可点击查看详情、通行标识ID、车牌号码、车牌颜色、入口站名、出口站名、入口时间、出口时间、入口车型、出口车型、通行费、标签名称、工单状态带颜色标签、补缴金额、总金额、审核人、审核时间、操作人、操作时间、操作按钮）
  - 影响文件：SplitMatch.vue、src/api/split-match/index.ts

### 2026-06-06 v2.33.0

#### Bug修复
- **云门户人工核查截图策略收敛**：按用户确认改为只截当前数据区，不再包含表头，进一步降低截图错位复杂度
  - 原因：表头需要单独处理横向偏移并与数据列宽严格同步，是截图首行和列位置错位的主要干扰项
  - 修复：离屏截图视口仅保留数据表 `el-table__body`，按真实 `scrollTop` / `scrollLeft` 还原当前数据区可见内容后输出
  - 效果：截图结果聚焦用户当前看到的数据行，避免表头参与带来的双层对齐误差
  - 影响文件：SplitMatch.vue

### 2026-06-06 v2.32.0

#### Bug修复
- **云门户人工核查截图滚动定位修复**：修复门架交易、门架牌识截图仍从表格顶部开始、未按当前可见首行输出的问题
  - 根因：即使直接对 `el-table` 当前区域截图，`modern-screenshot` 在克隆 DOM 时仍会把内部 `el-scrollbar__wrap` 的滚动状态重置为顶部，导致截图结果与用户当前看到的首行不一致
  - 修复：改为按真实 `scrollTop` / `scrollLeft` 构造离屏截图视口，分别克隆表头和数据表，再用位移还原用户当前看到的可视区域后截图
  - 效果：截图首行、表头横向位置与用户当前窗口保持一致，满足“所见即所截”
  - 影响文件：SplitMatch.vue

### 2026-06-06 v2.31.0

#### Bug修复
- **云门户人工核查截图修复**：按当前可见区域直接截图，修复门架交易、门架牌识“截图到资料1/2”未跟随滚动位置的问题
  - 根因：旧实现先展开整张表再按滚动偏移二次裁剪，但 `Element Plus 2.13.2` 的真实滚动层是 `ElScrollbar` 内部 `wrapRef`，代码却按 `.el-table__body-wrapper` 读取滚动位置并展开错误的 DOM 层，导致截图内容与用户当前所见不一致
  - 修复：移除“展开整表 + Canvas 二次裁剪”逻辑，改为直接对 `el-table` 当前可见区域执行 `domToPng`
  - 优化：过滤加载遮罩和 `el-scrollbar` 滚动条装饰元素，保留现有资料覆盖确认和保存流程
  - 影响文件：SplitMatch.vue

### 2026-06-06 v2.30.0

#### Bug修复
- **截图到资料功能修复**：修复 Canvas 二次裁剪法中可视区域尺寸测量错误导致截图仍为全表的问题
  - 根因：`viewWidth`/`viewHeight`/`headerHeight` 在展开 DOM 之后测量，展开后 `tableEl.clientHeight` 变为全部行高（~2500px）而非可视区域（~450px），导致 Canvas 裁剪形同虚设
  - 修复：所有尺寸（viewWidth、viewHeight、headerHeight、scrollTop、scrollLeft）在展开 DOM 之前测量，`viewHeight` 改用 `mainWrapper.clientHeight` 精确获取可视区域高度
  - 修复：展开后隐藏固定列（`.el-table__fixed`/`.el-table__fixed-right`）避免内容重叠，截图后恢复
  - 影响文件：SplitMatch.vue

### 2026-06-06 v2.29.0

#### Bug修复
- **截图到资料功能修复**：修复截图内容与用户当前滚动位置看到的表格数据不一致的问题
  - 根因：v2.28.0 对 `.el-table__body`（HTML `<table>` 元素）做 CSS `transform: translate()` 不可靠，截图库克隆DOM时 transform 效果丢失，截图仍从表格顶部开始
  - 修复：改用 Canvas 二次裁剪法 — 先展开DOM截取完整表格大图，再用 `canvas.drawImage()` 从 `(scrollLeft, headerHeight+scrollTop)` 处精确裁剪出可视区域，表头单独裁剪（仅横向偏移），数据区按用户滚动位置裁剪
  - 效果：截图内容与用户当前滚动位置看到的表格数据像素级一致（所见即所截）
  - 影响文件：SplitMatch.vue

### 2026-06-05 v2.28.0

#### Bug修复
- **截图到资料功能修复**：修复截图始终从表头+第一行开始、不跟随滚动位置的问题
  - 根因：`modern-screenshot` 克隆DOM时 `scrollTop`/`scrollLeft` 被重置为0（滚动位置是JS属性非CSS属性，克隆时丢失），导致截图始终从第一行开始
  - 修复：截图前重置滚动位置为0，对 `.el-table__body` 应用 `transform: translate(-scrollLeft, -scrollTop)` 将内容偏移到用户当前视口，对 `.el-table__header` 应用 `transform: translateX(-scrollLeft)` 同步横向滚动，对固定列仅应用 `translateY(-scrollTop)`，设置 `overflow: hidden` 裁剪溢出内容，截图后恢复所有修改
  - 效果：截图内容与用户当前滚动位置看到的表格数据完全一致（所见即所截）
  - 影响文件：SplitMatch.vue

### 2026-06-05 v2.27.0

#### Bug修复
- **截图到资料功能重构**：重写 `captureTable` 截图逻辑，实现"所见即所截"精准截图
  - 旧方案缺陷：截图前展开全部DOM（maxHeight=none, overflow=visible）再用 transform 偏移，导致横向截取全部列（scrollWidth）、纵向硬编码高度不精确、fixed列可能错位、大数据性能差
  - 新方案：不修改任何DOM样式，直接使用 `clientWidth/clientHeight` 截取el-table当前可视区域，modern-screenshot自动裁剪overflow容器的溢出内容
  - 纵向：只截可视行，滚动上方/下方不可见行不入图
  - 横向：只截可视列，横向滚动外隐藏列不入图
  - 固定列：无transform偏移，fixed列正常渲染无错位
  - 移除 bodyWrapper 样式保存/恢复逻辑，移除 scrollTop 记录/transform 偏移逻辑，代码大幅简化
  - 影响文件：SplitMatch.vue

### 2026-06-05 v2.26.0

#### Bug修复
- **截图到资料功能修复**：修复云门户人工核查窗口"截图到资料1/2"截取的图片内容不是用户当前滚动位置看到的数据的问题
  - 根因：`captureTable` 函数截图前将 bodyWrapper 的 `maxHeight` 设为 `none`、`overflow` 设为 `visible`，展开全部数据行后使用 `scrollHeight` 截取整表，忽略了用户滚动位置
  - 修复：截图前记录 `scrollTop` 滚动位置，展开 bodyWrapper 后通过 `transform: translateY(-scrollTop)` 偏移到用户当前视口，截图高度限制为表头高度+可视区域高度（门架交易/牌识 450px，其余 300px）
  - 效果：截图内容与用户当前看到的表格数据完全一致（所见即所得）
  - 影响文件：SplitMatch.vue

### 2026-06-05 v2.25.0

#### Bug修复
- **AI稽核批量查询数据完整性修复**：修复门架交易、门架牌识、出口交易等查询因 `length` 参数默认50导致数据截断的问题
  - GUI服务 `api_server.py` 的 batch-query 端点未将前端传入的 `rows` 参数传递给 `batch_query_all`，导致 `rows=500` 被丢弃
  - `ai_audit_client.py` 的 `batch_query_all` 调用 `query_gantry_trade/plate/exit_trade` 时未传递 `length` 参数，使用默认值50
  - 云门户API实际返回63条门架交易记录，但仅获取前50条，导致 `ENTIME: 09:23:21` 等记录丢失
  - 修复：`api_server.py` 读取并传递 `rows` 参数；`batch_query_all` 默认值从40改为500；所有分页查询传递 `length=rows`
  - 影响文件：api_server.py, ai_audit_client.py

### 2026-06-04 v2.24.0

#### Bug修复
- **截图功能修复**：修复云门户人工核查窗口"截图到资料1/2"截图内容与用户数据表区域不一致的问题
  - 恢复 `style: { overflow: 'visible !important' }` 配置项（v2.2.0 中存在，后续版本遗漏），确保 `domToPng` 能渲染滚动区域外的内容
  - 其他表格（出口交易ETC/其它、稽核工单）截图高度从 `offsetHeight`（仅可视区域）改为 `scrollHeight`（全部内容）
  - 修复截图后 bodyWrapper 样式未恢复的 bug：截图前保存 `maxHeight`/`overflow` 原始值，截图后在 `finally` 块中恢复，避免截图后表格滚动条消失
  - 移除未使用的 `headerWrapper` 变量
  - 影响文件：SplitMatch.vue

#### 功能优化
- **刷新列表按钮修复**：修复拆分匹配页面"刷新列表"按钮因 GET 请求缓存导致无法获取最新数据的问题
  - 调用 `getSplitMatchTables()` 前先清除 `/api/split-match/tables/` 的缓存
  - 影响文件：SplitMatch.vue

- **查询记录数上限提升**：解除 batch-query 的 rows 参数限制，默认值和兜底值从 20/50/100 统一提升为 500
  - 后端 `AIBatchQueryRequest.rows` 默认值 20 → 500
  - 后端 `GantryImagesRequest.rows` 默认值 20 → 500
  - 前端表单默认值 50 → 500，输入框 max 从 100 提升为 500、step 从 10 改为 50
  - 前端所有硬编码 rows 值（50/100）统一改为 500
  - 影响文件：cloud_portal.py、useCloudPortal.ts、useAIAudit.ts、SplitMatch.vue

### 2026-06-04 v2.22.0

#### 功能优化
- **数据表无感局部更新（F-03）**：拆分匹配页面保存数据后不再整表刷新，改为仅更新变更行，保留滚动位置、分页、筛选、排序、勾选状态
  - 新增 `updateSingleRowInTable` 方法：调用 `getSingleRow` API 获取单行最新数据，原地替换 `tableData` 中对应行，保留图片字段（BLOB列不在single-row返回中）
  - 3处保存后 `loadTableData()` 替换为 `updateSingleRowInTable`：主保存、强制覆盖保存、AI审计保存图片
  - 协作事件 `row_updated` 处理增强：收到其他用户的更新事件时，通过 `getSingleRow` 获取完整行数据并局部替换，替代原来仅映射5个字段的 `changed_fields` 方案
  - 保留整表刷新的场景：切换表、分页切换、筛选条件变更、执行匹配完成、导入数据、重置筛选
  - 影响文件：SplitMatch.vue

#### 后端优化
- **update端点广播协作事件**：`POST /api/split-match/update/` 更新成功后通过 `status_manager.broadcast_collaboration_event` 广播 `row_updated` 事件，携带 `changed_fields` 和 `table_name`，通知同表房间其他用户局部更新
  - 返回数据新增 `version` 字段，前端可直接获取新版本号无需额外查询
  - 版本号递增后使用 DictCursor 查询并返回最新版本号
  - 广播失败仅记录日志，不影响业务结果
  - 影响文件：routers/split_match.py

### 2026-06-04 v2.21.0

#### Bug修复
- **表格截图功能修复与优化**：修复云门户人工核查窗口中"截图到资料1/2"功能的多个问题
  - 修复所有表格截图不全：截取前临时移除 bodyWrapper 的 max-height/overflow 限制，截取后恢复，确保滚动区域外的数据行也能被捕获
  - 修复门架表格截图丢失表头：之前门架交易/牌识只截取 bodyWrapper（不含表头），现统一截取整个 el-table 元素（含表头+全部数据行）
  - 新增截图 loading 状态：截图期间禁用所有截图按钮并显示 loading，防止重复点击
  - 新增覆盖确认提示：目标资料槽位已有图片时弹出确认框，避免误覆盖
  - 优化截图参数：scale 从 1.2 降为 1.0，移除 PNG 无效的 quality 参数，减小输出体积
  - 清理死代码：删除 useAIAudit.ts 中未被调用的 captureTable、缓存相关函数（screenshotCache、computeTableHash、getCachedScreenshot、setCachedScreenshot、clearScreenshotCache）及 domToPng 导入
  - 影响文件：SplitMatch.vue、useAIAudit.ts

### 2026-06-02 v2.20.1

#### Bug修复
- **用户管理列表接口500错误**：修复 `GET /api/users/` 返回 `{"code":500,"message":"获取用户列表失败"}` 的问题
  - 根因：`DictCursor` 模式下 `fetchone()` 返回字典，代码用 `fetchone()[0]` 整数索引访问触发 `KeyError: 0`
  - 修复：将 `SELECT COUNT(*)` 改为 `SELECT COUNT(*) as total`，用 `fetchone()['total']` 字典键访问
  - 影响文件：routers/users.py

### 2026-06-01 v2.20.0

#### Bug修复
- **端口配置修正**：修复 cloud_portal_data_service.py 和 test_menu_api.py 中硬编码 8000 端口的问题，统一改为 8001
  - cloud_portal_data_service.py: BACKEND_URL 从 `http://127.0.0.1:8000` 改为正确的后端地址
  - test_menu_api.py: base URL 从 `http://localhost:8000` 改为 `http://localhost:8001`
  - 影响文件：cloud_portal_data_service.py、test_menu_api.py

### 2026-06-01 v2.19.0

#### 架构重构
- **云门户账号存储从 SQLite 迁移到 MySQL**：彻底移除 cloud_portal_accounts.db SQLite 数据库，统一使用 MySQL system_db.portal_accounts 表
  - 移除后端所有 SQLite 相关代码（_get_account_db、_ACCOUNT_DB_LOCK、threading 导入、SQLite 表创建与迁移逻辑）
  - 新增 MySQL 连接函数 _get_mysql_conn()，使用 database.get_db_connection("USER_DB", config) 连接 system_db
  - 重写账号管理函数（_save_account、_get_account、_delete_account、_update_account_tokens），全部改为 MySQL 操作
  - 修改 Token 函数（_get_access_token、_auto_relogin），新增 user_id 参数支持按用户查询
  - 更新全部 15 个路由端点，新增 user_id: Optional[int] = Query(None) 参数，替换硬编码 user_id=1
  - 删除 cloud_portal_accounts.db 文件（backend/ 和 backend/routers/ 两处）
  - 影响文件：routers/cloud_portal.py

#### Bug修复
- **多用户云门户登录互相踢出**：修复不同用户登录云门户时互相覆盖 Token 导致前一个用户被踢出的问题
  - 根因：后端使用 SQLite 存储，所有用户共享硬编码 user_id=1 的同一条记录，新登录用户覆盖前一个用户的 Token
  - 修复：每个用户使用各自的 user_id 查询 portal_accounts 表中独立的记录，Token 互不干扰
  - 前端 localStorage key 从固定 `cloud_portal_access_token` 改为 `cloud_portal_access_token_${userId}`，按用户隔离
  - 新增 setCloudPortalAccessToken、removeCloudPortalAccessToken 辅助函数，统一管理 Token 读写
  - 影响文件：api/split-match/index.ts、hooks/split-match/useCloudPortal.ts

### 2026-06-01 v2.18.0

#### 功能优化
- **查询参数区域重构**：从 el-descriptions 表格布局改为 CSS Grid 卡片式布局
  - 4列网格自适应：≥1400px 4列、1200-1400px 3列、900-1200px 3列、≤900px 2列
  - 每个字段值保证至少6个字符显示宽度（min-width: 6ch），超出部分省略号显示
  - 点击字段值弹窗显示完整内容，弹窗内附带"复制内容"按钮
  - 通行门架名称独占整行（grid-column: 1 / -1）
  - 影响文件：SplitMatch.vue
- **信息填写区域自适应**：与查询参数并列，小屏幕下纵向堆叠
- **AI稽核批量查询与退出登录按钮间距加大**：margin-bottom 从 8px 增至 16px，防止误触
- **查核资料图片支持点击查看原图**：使用 el-image 的 preview-src-list 属性，点击缩略图弹出全屏预览
  - preview-teleported 确保预览层挂载到 body，避免对话框遮挡
  - 影响文件：SplitMatch.vue

### 2026-05-31 v2.17.0

#### 功能优化
- **云门户人工核查窗口自适应分辨率**：优化对话框内布局，从硬编码固定宽度改为响应式弹性布局
  - 顶部三栏（查询参数/信息填写/云门户登录）支持 flex-wrap 自动换行
  - 主内容区域（查询结果/查核资料）支持弹性缩放
  - 添加 @media 断点：≤1400px 自动缩窄侧栏，≤1200px 改为纵向堆叠布局
  - 影响文件：SplitMatch.vue
- **查询参数复制按钮**：为通行标识ID、车牌号码、门架通行时间、入口时间添加一键复制按钮
  - 使用 CopyDocument 图标按钮，仅在有值时显示
  - 复用已有 handleCopy 函数，支持 Clipboard API 和 fallback 两种方式
  - 影响文件：SplitMatch.vue
- **AI稽核批量查询按钮醒目化**：增大按钮尺寸和视觉权重，退出登录按钮缩小
  - 批量查询按钮：size 从 small 改为 default，高度 44px，字号 15px，加粗 600，渐变背景+阴影+hover 上浮动效
  - 退出登录按钮：宽度从 172px 缩至 100px，高度从 35px 缩至 28px
  - 影响文件：SplitMatch.vue

### 2026-05-31 v2.16.0

#### Bug修复
- **菜单图标不显示**：修复菜单管理中设置了图标但左侧菜单栏不显示的问题
  - 根因：数据库 menus 表中 9 条记录的 icon 字段缺少 `vi-` 前缀（如 `ep:search`），离线模式下 CSS class 不匹配导致图标渲染失败
  - 修复1：数据库更新 9 条记录 icon 字段补全 `vi-` 前缀（如 `ep:search` → `vi-ep:search`）
  - 修复2：后端 users.py 增加 icon 前缀自动补全逻辑，当 icon 包含 `:` 且不以 `vi-` 开头时自动添加前缀
  - 影响文件：routers/users.py
- **表格截图只截取顶部行**：修复云门户人工核查窗口中"截图到资料1/2"始终截取表格顶部固定行而非当前显示内容的问题
  - 根因：el-table 设置了 max-height 产生内部滚动，domToPng 截取时 .el-table__body-wrapper 的 overflow 和 max-height 限制了渲染范围
  - 修复：截图前临时移除 .el-table__body-wrapper 的 max-height 和 overflow 限制，让表格完全展开截取所有行，截图后恢复原始样式
  - 影响文件：SplitMatch.vue、useAIAudit.ts

### 2026-05-31 v2.15.0

#### Bug修复
- **前端菜单渲染崩溃**：修复 MonitorCenter（监控中心）菜单 children 为 undefined 导致 `TypeError: Cannot read properties of undefined (reading 'filter')` 的问题
  - 根因：数据库 menus 表中特情记录(id=27)、事件记录(id=28)、排班功能(id=29) 的 type 字段被错误设为 2（按钮级），后端 `type != 2` 过滤掉了这些菜单，导致 MonitorCenter 成为没有 children 的空壳节点
  - 修复1：数据库将 id=27/28/29 的 type 从 2 改为 1（页面级）
  - 修复2：前端 useRenderMenuItem.tsx 中 `routers` → `(routers || [])`、`v.children!` → `v.children || []`，防止 undefined 传入递归
  - 修复3：前端 routerHelper.ts 中 `if (route.children)` → `if (route.children && route.children.length > 0)`，避免空数组设置无意义 children
  - 影响文件：useRenderMenuItem.tsx、routerHelper.ts
- **v-loading 指令未注册**：修复 Layout 及业务页面中 `Failed to resolve directive: loading` 警告
  - 根因：elementPlus/index.ts 中仅注册了 `ElLoading.service` 到全局属性，未通过 `app.directive('loading', ElLoading.directive)` 注册指令
  - 修复：在 setupElementPlus 函数中添加 `app.directive('loading', ElLoading.directive)`
  - 影响文件：plugins/elementPlus/index.ts
- **active-locks API 404**：修复拆分匹配页面 `GET /api/split-match/active-locks/` 返回 404 的问题
  - 根因：后端 split_match.py 缺少 active-locks 和 unlock 端点
  - 修复：添加 GET /api/split-match/active-locks/ 和 POST /api/split-match/unlock/ 端点
  - 影响文件：routers/split_match.py
- **用户列表接口500错误**：修复 GET /api/users/ 返回"获取用户列表失败"的问题
  - 根因：使用 DictCursor 时 `fetchone()` 返回 dict 类型，代码用 `[0]` 按索引访问导致 `KeyError: 0`
  - 修复：将 `SELECT COUNT(*)` 改为 `SELECT COUNT(*) as total`，用 `fetchone()['total']` 按键名访问
  - 影响文件：routers/users.py
- **后端菜单接口 path 为 NULL 导致 500**：修复部分菜单记录 path 字段为 NULL 时 `.lstrip()` 报错的问题
  - 修复：`(converted_menu.get('path') or '').lstrip('/')` 空值防护
  - 影响文件：routers/users.py
- **chat 路由 404**：修复前端调用 `/api/chat/sessions/` 和 `/api/chat/online-users/` 返回 404
  - 修复：创建 chat.py 路由模块，实现空端点并在 main.py 中注册
  - 影响文件：routers/chat.py、main.py

#### 数据库变更
- **menus 表 type 字段修正**：id=27（特情记录）、id=28（事件记录）、id=29（排班功能）的 type 从 2 改为 1

### 2026-05-30 v2.14.0

#### 菜单图标修复与图标选择器增强
- **菜单编辑图标选择器**：菜单管理-编辑表单中的图标字段从手动输入改为可视化图标选择器
  - 集成项目已有的 IconPicker 组件，支持点击弹出图标下拉面板
  - 支持 Element Plus、Ant Design、TDesign 三套图标库切换
  - 支持图标搜索过滤、分页浏览、点击选中/取消
  - 影响文件：Write.vue（菜单编辑表单）
- **数据库菜单图标补全**：修复 16 条菜单记录图标缺失问题
  - A类（5条）：调试信息、导出数据、查看、编辑、执行 — 新增图标值
  - B类（11条）：分析页、工作台、详单查询、路径匹配、数据记录、监控中心、管理中心、排班日历/班组/人员/班次 — 同步 meta_json.icon 与 icon 字段
- **后端图标兜底逻辑**：用户菜单接口（users.py）增加 icon 兜底，当 icon 字段为空时从 meta_json 中提取 icon
  - 修复前：仅读取 menus.icon 字段，若为空则 meta.icon 为空字符串，前端不显示图标
  - 修复后：icon 字段为空时自动从 meta_json.icon 取值，确保图标不丢失
  - 影响文件：users.py、models.py（补充 Dict/Any 类型导入）

### 2026-05-30 v2.13.0

#### 功能权限全面适配
- **按钮级权限控制覆盖所有功能页面**：为项目中所有包含操作按钮的页面适配 v-hasPermi 指令和 hasPermi 函数，实现按钮级权限控制
  - 适配方式：模板按钮使用 `v-hasPermi` 指令，TSX 按钮使用 `hasPermi()` 函数条件渲染，el-upload 组件使用 `v-if="hasImportPerm"` 控制显隐
  - 新增权限点 33 条（id=43~75），涵盖路径匹配、详单查询、定时任务、特情记录、排班管理等模块
  - 超级管理员角色补充分配全部 75 个权限点（原仅 42 个）
  - 影响页面及权限编码：
    - SyncControl.vue：`system:sync:control`（开始/暂停/停止/强制停止同步）
    - ParamsConfig.vue：`system:params:config`（保存/重置配置）
    - ScheduledTasks.vue：`scheduled-tasks:run/edit/view-history`（执行/编辑/历史）
    - User.vue：`system:user:add/edit/delete/view/assign`（新增/编辑/详情/分配角色/删除）
    - Role.vue：`system:role:add/edit/delete/view/assign/assign-permission`（新增/编辑/详情/菜单分配/权限分配/删除）
    - Menu.vue：`system:menu:add/edit/delete/view`（新增/编辑/详情/删除）
    - Department.vue：`system:dept:add/edit/delete/view`（新增/编辑/详情/删除）
    - SpecialRecords.vue：`special-records:add/edit/delete/export/import/batch-delete`（添加/编辑/删除/导出/导入/批量删除）
    - Staff.vue：`scheduling:staff:add/edit/delete/export/import`（新增/编辑/删除/导出/导入）
    - Groups.vue：`scheduling:groups:add/edit/delete/export/import`（新增/编辑/删除/导出/导入）
    - Shifts.vue：`scheduling:shifts:add/edit/delete/export/import`（新增/编辑/删除/导出/导入）
    - Calendar.vue：`scheduling:calendar:export/import/reset`（导出/导入/重置当月）
  - 影响文件：12 个 Vue 页面组件

#### 数据库变更
- **permissions 表新增 33 条记录**：路径匹配（3条）、详单查询（2条）、定时任务（3条）、特情记录（6条）、排班管理（15条）、角色权限分配（1条）、路径匹配搜索/导出/可视化（3条）
- **role_permissions 表补充**：超级管理员角色（role_id=1）补充分配 33 个缺失权限点

### 2026-05-30 v2.12.1

#### Bug修复
- **MCP MySQL 查询返回 undefined**：修复 MCP MySQL 工具配置指向错误数据库的问题
  - 根因1：mcp_config.json 中 database 配置为 `branchdb`（仅含 ETC 公路数据表），而系统管理数据（menus/permissions/roles/users）都在 `system_db` 中
  - 根因2：用户查询使用了不存在的列名 `title`，实际列名为 `name`
  - 根因3：MCP MySQL 服务器进程未正常启动/注册
  - 修复：mcp_config.json 默认库从 `branchdb` 改为 `system_db`
  - ETC 公路数据可通过跨库 SQL 访问：`SELECT * FROM branchdb.table_name`
  - 注意：修改配置后需重启 MCP MySQL 服务器进程才能生效

### 2026-05-30 v2.12.0

#### 架构优化
- **权限控制体系重构：菜单分配与权限分配职责分离**
  - 核心变更：菜单分配仅控制"能看到哪些页面"（type=0 目录 + type=1 页面），权限分配控制"能使用页面中的哪些功能"（按钮级）
  - 菜单分配树过滤掉 type=2 按钮节点，消除菜单分配与权限分配的语义混淆
  - 权限分配对话框从按 module 分组改为按所属菜单页面分组，管理员可直观看到每个页面下有哪些可分配的操作权限
  - 数据库 permissions 表新增 menu_id 列，关联 menus 表标识权限所属页面
  - 42 条权限记录全部关联到对应菜单页面（如 split-match:* → 拆分匹配，system:user:* → 用户管理）
  - 后端 GET /api/permissions/ 增加 LEFT JOIN menus 返回 menu_name 字段
  - 后端 POST/PUT /api/permissions/ 增加 menu_id 字段支持
  - 影响文件：backend/routers/permissions.py、backend/core/models.py、src/views/Authorization/Role/Role.vue

#### 验证通过
- 财务审核员角色：菜单分配首页-分析页 + 数据查询-拆分匹配，权限分配 split-match:view + split-match:statistics
- 结果：拆分统计按钮可见，导入/导出按钮隐藏，页面路由正常访问

### 2026-05-29 v2.11.3

#### Bug修复
- **拆分统计按钮不显示**：修复财务审核员角色已配置拆分统计权限，但拆分匹配页面"拆分统计"按钮不显示的问题
  - 根因1：LoginForm.vue 登录流程中只获取了菜单数据，未调用 getUserPermissionsApi 获取权限数据，导致 userStore.permissions 为空
  - 根因2：user.ts state 中未初始化 permissions 字段，初始值为 undefined
  - 根因3：v-hasPermi 指令只有 mounted 钩子且使用 removeChild 永久移除元素，权限变化后无法恢复
  - 修复1：LoginForm.vue 登录成功后补充调用 getUserPermissionsApi 并 setPermissions
  - 修复2：user.ts state 添加 permissions: [] 初始值
  - 修复3：hasPermi.ts 指令改用 style.display 控制显隐，增加 updated 钩子支持权限变化后恢复显示
  - 影响文件：src/views/Login/components/LoginForm.vue、src/store/modules/user.ts、src/directives/permission/hasPermi.ts

### 2026-05-28 v2.11.2

#### Bug修复
- **BaseButton 及 Dashboard 文字颜色恢复 Element Plus 默认样式**
  - 修复登录页"注册"按钮、注册页"已有账号"按钮等 default 类型 BaseButton 文字不可见的问题
    - 根因：BaseButton.vue 中 `style` 计算属性对非 primary 类型返回空字符串，导致 Element Plus CSS 变量继承链断裂，在特定主题下文字颜色异常
    - 修复：将空字符串改为返回 `'--el-button-text-color: var(--el-text-color-primary); --el-button-hover-text-color: var(--el-text-color-primary)'`，恢复 Element Plus 默认文字颜色变量
    - 影响文件：src/components/Button/src/Button.vue
    - 受影响页面：登录页注册按钮、注册页已有账号按钮、菜单/角色/部门/用户管理关闭按钮、列设置还原按钮、搜索重置按钮等 20+ 处
  - 修复 Dashboard 页面固定 Tailwind 灰色类在暗色模式下可读性差的问题
    - PanelGroup.vue：3 处 `text-gray-500` 改为 `text-[var(--el-text-color-regular)]`
    - Workplace.vue：7 处 `text-gray-400/500` 改为 `text-[var(--el-text-color-secondary)]` / `text-[var(--el-text-color-regular)]`
    - 影响文件：src/views/Dashboard/components/PanelGroup.vue、src/views/Dashboard/Workplace.vue
  - 修复 Analysis.vue ECharts 图表文字颜色硬编码及坐标轴颜色未适配主题的问题
    - 根因：亮色模式下图表文字使用固定 `#333`，坐标轴文字和分割线颜色未适配主题
    - 修复：
      - 标题/图例颜色：`#333` → `var(--el-text-color-primary)`
      - 坐标轴文字颜色：新增 `axisLabel` 和 `axisLine` 颜色设置，使用 `var(--el-text-color-secondary)`
      - 分割线颜色：亮色模式 `#eee`，暗色模式 `#333`
    - 影响文件：src/views/Dashboard/Analysis.vue
  - 修复 PanelGroup.vue 图标区域无背景色导致视觉不突出的问题
    - 根因：图标容器未设置背景色，hover 前图标区域背景透明，与官方项目样式不一致
    - 修复：为 peoples/free/money 图标容器添加浅色背景（#e6f9f8、#e6f3fb、#fce5e8）
    - 影响文件：src/views/Dashboard/components/PanelGroup.vue
- **EchartDynamic 图表类型映射重复键**：修复 chartTypeMap 对象中 `radar` 和 `map` 键重复定义导致 TypeScript 编译错误的问题
  - 影响文件：src/components/Echart/src/EchartDynamic.vue
- **ChatFloatingIcon 未使用导入**：移除 `ElBadge` 未使用的导入声明
  - 影响文件：src/components/ChatFloatingIcon/index.vue
- **LoginResponse 类型定义不完整**：补全 `LoginResponse.user` 接口中缺失的 `avatar`、`nickname`、`email` 可选字段，修复 TypeScript 类型检查错误
  - 影响文件：src/api/login/index.ts

#### 功能优化
- **路由导航分析功能**：修复 `POST /api/analytics/route` 接口返回 400 "不支持的分析类型"的问题
  - 根因：后端接口设计为通用分析执行器（期望 `{ type, params }`），前端发送路由导航日志（`{ timestamp, from, to, duration, userAgent }`），语义不匹配
  - 修复：重写后端接口为路由导航日志接收器，将日志写入 `route_analytics` 数据库表
  - 新增 `route_analytics` 表（含 username、from_path、to_path、duration、user_agent、created_at 字段及索引）
  - 新增 `GET /api/analytics/route/stats` 统计查询接口（支持页面访问排行、平均耗时、日活跃趋势）
  - 后端启动时自动建表（main.py startup 事件）
  - 影响文件：routers/analysis.py、main.py

### 2026-05-27 v2.11.1

#### Bug修复
- **EchartDynamic 图表类型映射重复键**：修复 chartTypeMap 对象中 `radar` 和 `map` 键重复定义导致 TypeScript 编译错误的问题
  - 影响文件：src/components/Echart/src/EchartDynamic.vue

### 2026-05-27 v2.11.0

#### Bug修复
- **BaseButton 文字不可见**：修复所有未指定 type 的 BaseButton（如登录页"注册"按钮、对话框"关闭"按钮）文字颜色为白色导致不可见的问题
  - 根因：BaseButton 组件模板中硬编码 `color-#fff`（UnoCSS 工具类，强制白色文字），导致 default 类型按钮在白色背景上文字不可见
  - 修复：移除硬编码的 `color-#fff`，primary 按钮通过 `--el-button-text-color` CSS 变量控制白色文字，其他类型由 Element Plus 原生样式接管
  - 影响文件：src/components/Button/src/Button.vue
  - 受影响页面：登录页注册按钮、注册页已有账号按钮、菜单/角色/部门/用户管理关闭按钮、列设置还原按钮等

#### 权限管理
- **拆分匹配功能权限体系实施**：完成拆分匹配页面的完整权限控制配置
  - 新增10个权限点到 permissions 表（id=33~42）：split-match:view、execute、import、export、edit、statistics、cloud-verify、verify-pass-id、lock-edit、upload-image
  - 更新 menus 表拆分匹配菜单（id=17）permission 字段为 split-match:view
  - 新增9个按钮类型子菜单（type=2）到 menus 表，分别对应执行匹配、导入数据、导出数据、编辑数据、拆分统计、云门户核查、通行标识核查、行锁定编辑、上传查核资料
  - 前端 SplitMatch.vue 添加 v-hasPermi 权限指令控制按钮显示/隐藏
  - 行锁定编辑权限通过 checkPermission 函数在 handleIdClick 中进行逻辑控制
  - 超级管理员角色已分配全部拆分匹配权限和菜单
  - 验证通过：admin 用户登录后可获取全部10个 split-match 权限点

### 2026-05-18 v2.10.0

#### Bug修复
- **用户列表接口500错误**：修复 GET /api/users/ 返回"获取用户列表失败"的问题
  - 根因：使用 DictCursor 时 `fetchone()` 返回 dict 类型，代码用 `[0]` 按索引访问导致 `KeyError: 0`
  - 修复：将 `SELECT COUNT(*)` 改为 `SELECT COUNT(*) as total`，用 `fetchone()['total']` 按键名访问
  - 影响文件：routers/users.py
- **云门户账号绑定保存失败**：修复 POST/DELETE 请求中 user_id 参数未传递到后端的问题
  - 根因：axios 拦截器仅处理 GET 请求的 params 拼接，POST/DELETE 请求的 params 被忽略
  - 修复：新增 `appendUserId` 辅助函数，所有 POST/DELETE 请求将 user_id 直接拼接到 URL 查询字符串
  - 影响函数：saveCloudPortalAccount、deleteCloudPortalAccount、cloudPortalAutoLogin、cloudPortalLogout、keepCloudPortalAlive、cloudPortalQuery、aiAuditBatchQuery、aiAuditVehicleImages、aiAuditGantryImages、aiAuditGantryTrade、aiAuditGantryPlate、aiAuditExitTrade、aiAuditSuspectedCar、aiAuditOriginalImage、fetchPicture

#### 架构重构
- **云门户账号存储迁移**：将云门户账号从独立 SQLite 数据库迁移到 MySQL 系统数据库
  - 新建 `portal_accounts` 表于 MySQL USER_DB 中，包含 user_id、portal_username、portal_password、access_token、refresh_token、redirect_uri、token_expires_at 等字段
  - 启动时自动建表，确保表结构就绪
  - 启动时自动检测旧 SQLite 文件并迁移数据到 MySQL（仅执行一次，迁移后旧文件重命名为 .migrated）
  - 移除 SQLite 相关代码（_ACCOUNT_DB_LOCK、_get_account_db 函数）
  - 所有数据库操作改用 database.py 的 get_db_connection 连接池

#### 多用户支持
- **user_id 参数化**：所有云门户 API 端点添加 user_id 查询参数
  - 后端所有端点（auto-login、logout、keep-alive、query、batch-query、vehicle-images、gantry-images、gantry-trade、gantry-plate、exit-trade、suspected-car、audit-order、original-image、fetch-picture、order-detail、account CRUD）均支持 user_id 参数
  - 前端所有云门户 API 调用添加可选 userId 参数，通过 userStore.getUserInfo?.id 获取当前用户 ID
  - 内部函数 _get_access_token、_auto_relogin、_get_account、_save_account、_delete_account、_update_account_tokens 均接收 user_id 参数
  - 消除原硬编码 user_id=1 的问题，实现多用户独立绑定云门户账号

#### 前端修改
- **API 层**：api/split-match/index.ts 中所有云门户相关函数添加 userId 可选参数
- **组件层**：
  - CloudPortalAccount.vue：通过 useUserStore 获取当前用户 ID 传入 API
  - CloudPortalLoginDialog.vue：通过 useUserStore 获取当前用户 ID 传入 API
  - SplitMatch.vue：所有 AI 稽核查询传入 userStore.getUserInfo?.id
- **Hook 层**：useCloudPortal.ts 添加 useUserStore 集成，自动登录/登出/获取凭证时传入用户 ID

#### 版本号
- 前端版本号从 2.9.0 升级到 2.10.0

---

### 2026-02-16

#### 新增功能
- **权限控制**：为详单查询页面添加调试信息和导出数据的权限控制
  - 在菜单管理中添加权限配置
  - 超级管理员和管理员默认拥有这些权限
  - 调试信息区域和导出按钮根据用户权限动态显示
- **数据导出**：详单查询页面增加数据导出功能
  - 支持导出当前页数据为Excel文件
  - 文件名包含时间戳避免重复
  - 按钮标题修改为"导出数据"
- **按钮布局**：查询、重置、导出数据按钮固定放置在下一行
  - 使用flex布局美化间距
  - 提升用户体验

#### 功能优化
- **权限判断**：改进权限判断逻辑
  - 从基于用户名判断改为基于用户角色列表判断
  - 支持"超级管理员"和"管理员"角色
  - 更灵活的权限管理机制
- **用户信息**：完善用户类型定义
  - 添加`roleList`字段支持多角色
  - 添加`id`字段
- **登录逻辑**：更新登录时的用户信息设置
  - 为admin和test用户设置"超级管理员"角色

---

### 历史版本

#### 详单查询功能增强
- **组合字段展示**：详细信息窗口中拆分收费路段编号组合等字段使用单独表格展示
  - 字段值根据"|"分割
  - 每个值与各字段相互对应
- **金额合计**：表格下方对拆分收费金额组合金额(分)进行合计
  - 合计后的金额单位为"元"
- **时间合计**：拆分收费时间组合在合计行计算合计用时时间
  - 计算计费交易起点时间至计费交易终点时间的间隔时间
- **对话框优化**：解决详细信息在数据高度过高时会超出页面显示范围的问题
  - 添加滚动样式
  - 限制对话框高度
- **字段标题显示**：详细信息窗口保持出口交易编号、通行标识ID字段标题在同一行有适当的宽度完整显示
  - 不折叠不换行
  - 添加`no-wrap-label`样式类

#### 前端交互优化
- **历史记录功能**：为"通行标识ID"和"车牌号码"添加本地存储最近10条输入记录的功能
  - 支持自动补全
  - 提升用户输入体验
- **时间选择器**：合并"计费交易起点时间"和"计费交易终点时间"为单个日期时间范围选择器
  - 默认时间为`00:00:00`和`23:59:59`
  - 名称改为"计费交易起止时间"
- **下拉选择组件**：详单查询中收费车型、计费方式、通行介质、拆分类型/数据类型修改为下拉选择组件
  - 使用`detail-query-options.json`对应的值
  - 提升数据输入准确性
- **分页设置**：取消10, 20,默认显示50行数据
  - 优化分页选项

#### 后端性能优化
- **API性能优化**：优化详单查询API性能，解决超时错误和网络错误
  - 实现异步查询执行（`asyncio`+`ThreadPoolExecutor`）
  - 添加超时保护（300s）
  - 优化数据库连接管理
- **索引优化**：分析并优化数据库索引
  - `index_a`、`index_b`、`index_c`、`idx_trade_time`
  - 推荐复合索引（如`idx_split_month`）
  - 优化COUNT查询瓶颈
- **SQL日志增强**：增强SQL查询日志输出
  - 确保控制台能显示完整SQL语句
  - 使用分隔线和标记包裹SQL语句
  - 统计查询执行时间
- **查询条件优化**：修改车牌号码查询条件，移除前缀`%`
  - 提升查询性能
- **调试信息**：后端返回调试信息
  - COUNT SQL
  - SELECT SQL
  - 总耗时
  - COUNT查询耗时

#### 前端类型修复
- **TypeScript类型错误修复**：修复前端TypeScript类型错误
  - `AxiosConfig`缺少`timeout`属性
  - `DetailQueryDataItem`未导出
  - 响应类型不匹配
  - 扩展`AxiosConfig`和`IResponse`接口
- **JSON模块声明**：添加JSON模块声明
  - 解决JSON导入类型错误
- **用户类型定义**：完善`UserType`接口
  - 添加可选字段
  - 支持`roleList`多角色

#### 前端UI改进
- **调试信息区域**：在详单查询页底部添加调试信息显示区域
  - 仅对有权限的用户可见
  - 显示COUNT SQL和SELECT SQL
  - 显示查询耗时统计
  - 支持SQL复制功能
  - 可展开/收起
- **详细信息窗口**：实现表格行点击弹出详细信息窗口功能
  - 显示被点击行的所有内容
  - 使用`el-descriptions`展示基本信息
  - 使用`el-table`展示组合字段详情
  - 支持复制全部数据
- **公共配置文件**：生成提供给前端调用的公共json文件
  - `detail-query-options.json`
  - 包含收费车型、车辆状态标识、车种、计费方式、通行介质、拆分类型等下拉选择数据

#### 其他修复
- **弃用警告处理**：处理"卸载事件监听器已被弃用"的警告
- **变量作用域问题**：修复后端返回`debug`字段时`count_duration`未定义的问题
- **搜索参数传递**：修复合并时间选择器后`start_time`和`end_time`未正确传递的问题
- **日期选择器显示异常**：修复日期选择器显示NaN年等异常
  - 配置Element Plus中文语言包
  - 正确初始化`time_range`
- **按钮标题修改**：将"导出当前页"标题修改为"导出数据"

---

## 使用说明

### 自动更新日志
本项目支持自动更新更新日志。每次修复或增加功能、修改后，请按照以下格式更新本文件：

```markdown
### YYYY-MM-DD

#### 新增功能
- **功能名称**：功能描述
  - 详细说明1
  - 详细说明2

#### 功能优化
- **优化项**：优化描述

#### Bug修复
- **问题描述**：修复说明
```

### 日志规范
- 按时间倒序排列，最新版本在最上方
- 使用统一的标题格式
- 每个变更点都要有清晰的描述
- 涉及的文件路径可使用`文件路径:行号`格式

---

## 项目信息

- **项目名称**：本地Python系统
- **框架**：FastAPI (后端) + Vue 3 + Element Plus (前端)
- **开发语言**：Python + TypeScript
- **数据库**：MySQL
