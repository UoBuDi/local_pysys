# 项目更新日志

## [最新版本]

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
