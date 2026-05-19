# 项目更新日志

## [最新版本]

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
