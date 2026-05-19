# 云门户系统 API 接口文档

**版本：v2.1.0 (2026-05-05)**

> **重要变更说明：**
> - ✅ GUI服务已切换至**完全无状态模式**
> - ✅ 所有业务接口统一使用`access_token`认证（不再需要session_id）
> - ✅ 后端自动注入Token到转发请求
> - ✅ 会话管理已移至后端数据库
> - ⚠️ keep-alive机制暂时简化为Token有效性检查（后续由用户决定是否改为纯Token续期）

## 一、系统概述

云门户系统是湖南省高速公路电子收费系统的统一认证与稽核平台，本系统通过后端代理方式与云门户外部 API 交互，实现以下功能：

- SSO 统一认证登录（含验证码、自动登录）
- AI 稽核数据查询（车辆图库、门架交易、门架牌识、出口交易、嫌疑车、工单详情）
- 图片代理获取与保存
- 云门户账号管理

**架构特点（v2.1.0）：**
- **完全无状态设计**：GUI服务不维护任何会话状态，每次请求创建临时客户端实例
- **Token驱动认证**：所有业务接口使用access_token进行身份验证
- **后端Token注入**：后端从数据库读取Token并自动注入到转发请求中
- **UUID临时使用**：仅在登录验证码校验时使用，用完即弃
- **OAuth2标准**：基于JWT Token实现会话管理

## 二、外部 API 地址

| 服务 | 基础地址 |
|------|----------|
| SSO 认证服务 | `http://api.hngsetc.com` |
| 验证码服务 | `http://api.hngsetc.com/captcha-server` |
| 用户服务 | `http://home.hngsetc.com/gateway/user-server` |
| AI 稽核服务 | `http://twaudit.hngsetc.com/gateway/ai-audit-server` |
| 图片服务 | `http://api.hngsetc.com/picture-server` |
| SSO 登录页 | `http://sso.hngsetc.com` |
| 首页 | `http://home.hngsetc.com` |
| 稽核前端 | `http://twaudit.hngsetc.com/aiAuditWeb` |

## 三、认证流程

### 3.1 SSO 登录流程（v2.1.0 无状态设计）

```
1. 获取验证码 → GET /api/cloud-portal/captcha
   ↓ GUI服务创建临时PortalClient实例
   ↓ 返回 uuid (一次性使用)
2. 用户输入验证码 + 提交登录
   ↓ POST /api/cloud-portal/login (包含uuid, username, password, captcha)
   ↓ GUI服务使用临时客户端完成登录（用完即弃）
3. SSO 登录成功 → 返回 access_token, refresh_token
   ↓ 后端保存Token到数据库portal_accounts表
4. 后续业务请求 → POST /api/cloud-portal/ai-audit/xxx
   ↓ 后端从数据库读取Token并注入到请求数据
   ↓ GUI服务使用Token创建临时AIAuditClient执行查询
5. 响应返回给前端（全程无需session_id）
```

### 3.2 v2.1.0 核心变更

**已废弃的参数：**
- ❌ `session_id` - 所有接口不再需要此参数

**新增/强制的参数：**
- ✅ `access_token` - 所有业务接口必须携带（由后端自动注入）

**受影响的接口列表：**

| 接口路径 | 变更类型 | 说明 |
|----------|----------|------|
| `/api/portal/query` | 参数变更 | session_id → access_token |
| `/api/portal/status` | 参数变更 | session_id → access_token |
| `/api/portal/session/check` | 参数变更 | session_id → access_token |
| `/api/portal/logout` | 简化 | 不再需要任何参数 |
| `/api/portal/keep-alive` | 参数变更 | session_id → access_token，简化为Token有效性检查 |
| `/api/portal/sessions` | 行为变更 | 始终返回空列表（兼容性保留） |
| `/api/portal/ai-audit/*` (10个) | 参数变更 | 全部使用access_token |
| `/api/portal/order-detail` | 参数变更 | session_id → access_token |

**保持不变的接口：**
- ✅ `/api/portal/captcha` - 仍不需要认证
- ✅ `/api/portal/login` - 使用uuid验证码，不涉及session/token
- ✅ `/api/portal/captcha/ocr/*` - OCR功能不受影响
- ✅ `/api/portal/health` - 健康检查不变
- ✅ 静态数据接口（branch-centers, road-sections, gantry-list）- 不变

### 3.2 关键参数

| 参数 | 值 | 说明 |
|------|----|------|
| SSO_CLIENT_ID | `7d569fe611e44189b19dc286b3f0a8a6` | 首页SSO客户端ID |
| AI_AUDIT_CLIENT_ID | `c3a92b6963d84a3e827f3d79119a27a5` | AI稽核SSO客户端ID |
| TENANT_ID | `1d68da3aa0a54f158fd6dab013a81d48` | 租户ID |
| 密码加密 | MD5 | 登录密码需MD5加密后传输 |

### 3.3 Token机制说明

**Token类型：**
- **access_token**：访问令牌，用于API调用，有效期约2小时
- **refresh_token**：刷新令牌，用于续期access_token

**存储位置：**
- 后端SQLite数据库：`portal_accounts`表
- 字段：`access_token`, `refresh_token`, `redirect_uri`, `token_expires_at`

**有效性检查：**
- 解析JWT payload中的`exp`字段
- 与当前时间戳比较判断是否过期

## 四、后端代理 API 接口

### 4.1 验证码

**GET** `/api/cloud-portal/captcha`

获取云门户验证码图片。

响应：
```json
{
  "code": 200,
  "message": "获取验证码成功",
  "data": {
    "img": "base64-encoded-image",
    "uuid": "captcha-uuid"
  }
}
```

**说明：**
- 无需任何参数
- 返回的`uuid`仅用于本次登录的验证码提交
- 用完即弃，不需要持久化存储

### 4.2 登录

**POST** `/api/cloud-portal/login`

使用验证码登录云门户。

请求体：
```json
{
  "uuid": "string",
  "username": "string",
  "password": "string",
  "captcha": "string"
}
```

响应：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user_info": {
      "id": 1,
      "username": "xxx",
      "real_name": "xxx"
    },
    "access_token": "jwt-token-string",
    "refresh_token": "refresh-token-string",
    "redirect_uri": "http://..."
  }
}
```

**说明：**
- 登录成功后，后端自动保存Token到数据库
- 前端通过`cloudPortalLoggedIn`状态判断是否已登录
- 不再返回或使用session_id

### 4.3 自动登录

**POST** `/api/cloud-portal/auto-login`

使用 OCR 自动识别验证码登录，最多重试5次。

请求体：
```json
{
  "username": "string",
  "password": "string"
}
```

响应（成功）：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": { "user_info": { ... } }
}
```

响应（需手动验证码）：
```json
{
  "code": 201,
  "message": "自动登录失败，需要手动输入验证码",
  "data": {
    "img": "base64",
    "uuid": "string",
    "need_captcha": true
  }
}
```

**说明：**
- 完全自动处理验证码获取和识别
- 无需前端传递任何会话标识
- 失败时返回新的验证码供手动输入

### 4.4 会话状态

**GET** `/api/cloud-portal/status`

查询云门户会话状态（基于Token有效性）。

响应：
```json
{
  "code": 200,
  "data": {
    "logged_in": true,
    "has_valid_token": true,
    "token_expires_at": 1234575090
  }
}
```

**说明：**
- 通过检查数据库中Token的有效性判断登录状态
- 不依赖内存中的session状态
- 支持多实例部署（无状态）

### 4.5 健康检查

**GET** `/api/cloud-portal/health`

检查云门户服务是否可达。

响应：
```json
{
  "code": 200,
  "data": { "status": "healthy", "service": "cloud-portal", "version": "2.0.0" }
}
```

### 4.6 登出

**POST** `/api/cloud-portal/logout`

登出云门户，清除本地Token。

请求体：
```json
{}
```

**说明：**
- 清除数据库中保存的Token信息
- 通知GUI服务销毁远程会话
- 无需传递session_id

### 4.7 保持活跃

**POST** `/api/cloud-portal/keep-alive`

保持Token有效，防止过期。

请求体：
```json
{}
```

**说明：**
- 定期调用以维持会话活跃状态
- 可结合Token刷新机制使用

### 4.8 通用查询

**POST** `/api/cloud-portal/query`

通用查询入口，通过 `type` 字段区分查询类型。

请求体：
```json
{
  "query_params": {
    "type": "vehicle_images | gantry_trade | gantry_plate",
    "...": "各类型对应参数"
  }
}
```

**说明：**
- 后端从数据库读取Token进行认证
- 无需前端传递任何会话标识

## 五、AI 稽核接口

### 5.1 批量查询

**POST** `/api/cloud-portal/ai-audit/batch-query`

一次性获取车辆图库、门架交易、门架牌识等全部数据。

请求体：
```json
{
  "plate_number": "苏GG6382",
  "entry_time": "2025-12-01 00:00:00",
  "gate_time": "2025-12-02 23:59:59",
  "pass_id": "可选",
  "hours": 2,
  "rows": 12
}
```

响应：
```json
{
  "code": 200,
  "data": {
    "time_range": { "start_time": "...", "end_time": "..." },
    "vehicle_images": { "success": true, "total": 10, "images": [...] },
    "gantry_trade": { "success": true, "total": 5, "records": [...] },
    "gantry_plate": { "success": true, "total": 8, "records": [...] },
    "exit_trade_etc": { "success": false, "total": 0, "records": [] },
    "exit_trade_other": { "success": false, "total": 0, "records": [] },
    "audit_order": { "success": false, "total": 0, "records": [] },
    "suspected_car": { "success": false, "trade_list": [] },
    "errors": []
  }
}
```

**说明：**
- 后端自动附加Token进行认证
- 前端只需传递业务参数

### 5.2 车辆图库

**POST** `/api/cloud-portal/ai-audit/vehicle-images`

外部API: `POST http://twaudit.hngsetc.com/gateway/ai-audit-server/ExternalAudit/travelTrack.json`

请求体：
```json
{
  "plate_number": "苏GG6382",
  "start_time": "2025-12-01 00:00:00",
  "end_time": "2025-12-02 23:59:59",
  "page": 1,
  "page_size": 12,
  "sort": "picTime DESC"
}
```

### 5.3 门架图库

**POST** `/api/cloud-portal/ai-audit/gantry-images`

外部API: `POST http://twaudit.hngsetc.com/gateway/ai-audit-server/ExternalAudit/travelTrack.json`

请求体：
```json
{
  "station_id": "G005543006007320010",
  "start_time": "2025-12-01 00:00:00",
  "end_time": "2025-12-02 23:59:59",
  "rows": 12,
  "start": 0,
  "sort": "picTime DESC"
}
```

### 5.4 门架交易

**POST** `/api/cloud-portal/ai-audit/gantry-trade`

外部API: `POST http://twaudit.hngsetc.com/gateway/ai-audit-server/tool/query/gantry/trade`

请求体：
```json
{
  "query_value": "苏GG6382",
  "start_time": "2025-12-01 00:00:00",
  "end_time": "2025-12-02 23:59:59"
}
```

### 5.5 门架牌识

**POST** `/api/cloud-portal/ai-audit/gantry-plate`

外部API: `POST http://twaudit.hngsetc.com/gateway/ai-audit-server/tool/query/picInfo/query`

请求体：
```json
{
  "plate_number": "苏GG6382",
  "start_time": "2025-12-01 00:00:00",
  "end_time": "2025-12-02 23:59:59"
}
```

### 5.6 出口交易

**POST** `/api/cloud-portal/ai-audit/exit-trade`

外部API: `POST http://twaudit.hngsetc.com/gateway/ai-audit-server/tool/query/exit/trade`

请求体：
```json
{
  "query_value": "苏GG6382",
  "start_time": "2025-12-01 00:00:00",
  "end_time": "2025-12-02 23:59:59",
  "trade_type": 1
}
```

### 5.7 嫌疑车

**POST** `/api/cloud-portal/ai-audit/suspected-car`

外部API: `POST http://twaudit.hngsetc.com/gateway/ai-audit-server/tool/query/suspectedCar`

请求体：
```json
{
  "vehicle_or_pass_id": "苏GG6382",
  "start_time": "2025-12-01 00:00:00",
  "end_time": "2025-12-02 23:59:59"
}
```

### 5.8 工单详情

**GET** `/api/cloud-portal/ai-audit/order-detail`

外部API: `GET http://twaudit.hngsetc.com/gateway/ai-audit-server/ExternalAudit/orderDetail.json`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_id | string | 是 | 工单ID |

**说明：**
- 仅需order_id参数
- 后端自动附加Token认证

### 5.9 选择图片

**POST** `/api/cloud-portal/ai-audit/select-images`

从图库中按门架ID选择对比图片。

请求体：
```json
{
  "images": [{ "stationId": "...", "bigPositivePic": "...", ... }],
  "gantry_ids": ["G005543006007320010", "G007643003003010010"]
}
```

### 5.10 保存核查图片

**POST** `/api/cloud-portal/ai-audit/save-images`

保存核查结果到本地数据库。

请求体：
```json
{
  "table_name": "202512",
  "record_id": "123",
  "image1_base64": "data:image/jpeg;base64,...",
  "image2_base64": "data:image/jpeg;base64,...",
  "review_status": "已核查",
  "check_pass_id": "020000440101610474537720251129081902",
  "special_situation": "无",
  "check_split": "否",
  "remark": "备注",
  "clear_empty": false
}
```

### 5.11 获取原始图片

**POST** `/api/cloud-portal/ai-audit/original-image`

代理获取云门户原始图片。

请求体：
```json
{
  "picture_path": "http://api.hngsetc.com/picture-server/api/realPicture/get?..."
}
```

### 5.12 代理获取图片

**POST** `/api/cloud-portal/fetch-picture`

通用图片代理接口。

请求体：
```json
{
  "picture_url": "http://..."
}
```

### 5.13 分中心列表

**POST** `/api/cloud-portal/ai-audit/branch-centers`

获取分中心列表（用于数据同步）。

**说明：**
- 无需参数
- 后端自动认证并请求数据

### 5.14 路段列表

**POST** `/api/cloud-portal/ai-audit/road-sections`

获取路段列表。

请求体：
```json
{
  "center_no": "分中心编号"
}
```

### 5.15 门架列表

**POST** `/api/cloud-portal/ai-audit/gantry-list`

获取门架列表。

请求体：
```json
{
  "road_section_no": "路段编号"
}
```

## 六、云门户账号管理

### 6.1 获取账号

**GET** `/api/cloud-portal-account/`

获取已保存的云门户账号信息。

响应：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "portal_username": "xxx",
    "portal_password": "xxx",
    "access_token": "当前有效的访问令牌或null",
    "refresh_token": "刷新令牌或null",
    "redirect_uri": "重定向URI或null",
    "token_expires_at": "过期时间戳或null",
    "is_valid": true/false
  }
}
```

**说明：**
- 返回完整的Token信息及有效性状态
- 前端可据此判断是否需要重新登录

### 6.2 保存账号

**POST** `/api/cloud-portal-account/`

请求体：
```json
{
  "portal_username": "string",
  "portal_password": "string"
}
```

### 6.3 删除账号

**DELETE** `/api/cloud-portal-account/`

### 6.4 获取凭据

**GET** `/api/cloud-portal-account/credentials`

获取含密码明文的完整凭据（用于自动登录）。

**已废弃接口：**

~~### 6.5 更新会话~~

~~**POST** `/api/cloud-portal-account/session`~~

> ⚠️ **此接口已废弃**
>
> 该接口用于更新session_id，在v2.0版本中已完全移除。
>
> **替代方案：**
> - 登录成功后Token自动保存到数据库
> - 所有业务接口自动从数据库读取Token
> - 无需手动维护会话状态

## 七、外部 API 详细说明

### 7.1 验证码获取

```
GET http://api.hngsetc.com/captcha-server/api/captcha?{timestamp}
Headers:
  Referer: http://sso.hngsetc.com/
Response:
  { "img": "base64-image", "uuid": "captcha-uuid" }
Cookie:
  JSESSIONID=xxx (GUI服务内部管理)
```

### 7.2 验证码校验

```
GET http://api.hngsetc.com/captcha-server/form/validate?captcha={code}&uuid={uuid}
Headers:
  Cookie: JSESSIONID=xxx
  Referer: http://sso.hngsetc.com/sso/login.html?client_id=7d569fe611e44189b19dc286b3f0a8a6
Response:
  { "code": "200", "msg": "验证成功" }
```

### 7.3 SSO 登录

```
POST http://api.hngsetc.com/oauth-server/sso/ssoLogin
Content-Type: application/x-www-form-urlencoded
Body:
  global_client=sso-web
  client_id=7d569fe611e44189b19dc286b3f0a8a6
  username=xxx
  password=md5(xxx)
  redirect_uri=
Response:
  {
    "code": { "code": "0", "msg": "操作成功" },
    "result": {
      "global_access_token": "xxx",
      "global_refresh_token": "xxx",
      "redirect_uri": "http://home.hngsetc.com/...?token=xxx&refresh_token=xxx"
    }
  }
```

### 7.4 获取用户信息

```
GET http://home.hngsetc.com/gateway/user-server/user/getUserInfo.json?tenantId=1d68da3aa0a54f158fd6dab013a81d48
Headers:
  Authorization: Bearer {access_token}
Response:
  {
    "code": { "code": "0" },
    "result": { "user": { "user_id": 1, "username": "xxx", "real_name": "xxx" } }
  }
```

### 7.5 换取 AI 稽核 Token

```
GET http://api.hngsetc.com/oauth-server/sso/authorize?client_id=c3a92b6963d84a3e827f3d79119a27a5&response_type=token&redirect_uri=http://twaudit.hngsetc.com/aiAuditWeb/index.html
Headers:
  Authorization: Bearer {home_access_token}
Response:
  302 Redirect → Location: http://twaudit.hngsetc.com/aiAuditWeb/index.html?token={audit_token}&refresh_token={refresh_token}
```

### 7.6 AI 稽核 - 车辆图库

```
POST http://twaudit.hngsetc.com/gateway/ai-audit-server/ExternalAudit/travelTrack.json
Headers:
  Authorization: Bearer {audit_token}
  Content-Type: application/json
Body:
  {
    "vehPlate": "苏GG6382",
    "vehPlateColor": "",
    "rows": 12,
    "start": 0,
    "sort": "picTime DESC",
    "startTime": "2025-12-01 00:00:00",
    "endTime": "2025-12-02 23:59:59"
  }
```

### 7.7 AI 稽核 - 门架交易

```
POST http://twaudit.hngsetc.com/gateway/ai-audit-server/tool/query/gantry/trade
Headers:
  Authorization: Bearer {audit_token}
  Content-Type: application/json
Body:
  {
    "draw": 1,
    "start": 0,
    "length": 10,
    "jsonParam": "{\"queryValue\":\"苏GG6382\",\"startTime\":\"2025-12-01 00:00:00\",\"endTime\":\"2025-12-02 23:59:59\"}"
  }
```

### 7.8 AI 稽核 - 门架牌识

```
POST http://twaudit.hngsetc.com/gateway/ai-audit-server/tool/query/picInfo/query
Headers:
  Authorization: Bearer {audit_token}
  Content-Type: application/json
Body:
  {
    "draw": 1,
    "start": 0,
    "length": 10,
    "jsonParam": "{\"vehPlate\":\"苏GG6382\",\"startTime\":\"2025-12-01 00:00:00\",\"endTime\":\"2025-12-02 23:59:59\"}"
  }
```

### 7.9 图片获取

```
GET http://api.hngsetc.com/picture-server/api/realPicture/get?stationId={id}&path={path}
Headers:
  Authorization: Bearer {token}
  Referer: http://twaudit.hngsetc.com/
Response: image/jpeg binary
```

## 八、数据存储与Token管理

### 8.1 数据库表结构

**表名：** `portal_accounts`

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键自增 |
| user_id | INTEGER | 用户ID（默认为1） |
| portal_username | TEXT | 云门户用户名 |
| portal_password | TEXT | 云门户密码（加密存储） |
| access_token | TEXT | 访问令牌（JWT） |
| refresh_token | TEXT | 刷新令牌 |
| redirect_uri | TEXT | 重定向URI |
| token_expires_at | REAL | Token过期时间戳（Unix时间） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**已废弃字段：**
- ~~`portal_session_id`~~ - 已在v2.0中移除

### 8.2 数据库迁移

系统支持自动从旧版表结构迁移：

**检测条件：**
```sql
-- 检测是否存在旧字段
SELECT * FROM pragma_table_info('portal_accounts') WHERE name = 'portal_session_id';
```

**迁移操作：**
```sql
-- 1. 备份旧表
ALTER TABLE portal_accounts RENAME TO portal_accounts_old;

-- 2. 创建新表（不含portal_session_id）
CREATE TABLE portal_accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL DEFAULT 1,
  portal_username TEXT NOT NULL,
  portal_password TEXT NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  redirect_uri TEXT,
  token_expires_at REAL,
  created_at TEXT DEFAULT (datetime('now', 'localtime')),
  updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 3. 迁移数据（忽略旧字段）
INSERT INTO portal_accounts (user_id, portal_username, portal_password)
SELECT user_id, portal_username, portal_password FROM portal_accounts_old;

-- 4. 删除旧表
DROP TABLE portal_accounts_old;
```

### 8.3 Token生命周期

```
[登录成功] → [保存Token到DB] → [业务请求使用Token]
     ↓                              ↓
[Token即将过期] ← [检查有效性] ← [定期轮询]
     ↓
[刷新Token] 或 [重新登录]
```

**关键函数：**
- `_update_account_tokens()` - 更新或部分更新Token信息
- `_is_token_valid()` - 检查Token是否有效（基于exp字段）
- `_get_account()` - 获取账号信息（含Token）

## 九、错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| 200 | 成功 | 正常处理 |
| 201 | 需要手动输入验证码 | 显示验证码给用户 |
| 400 | 请求参数错误 | 检查必填字段 |
| 401 | 未登录或Token过期 | 引导用户重新登录 |
| 404 | GUI服务不可达 | 检查GUI服务是否启动 |
| 500 | 服务器内部错误 | 查看日志定位问题 |
| 502 | 上游服务错误 | 重试或稍后再试 |

## 十、版本历史

### v2.0.0 (2026-05-05)

**重大变更：**
- ✅ 完全移除session_id依赖，采用无状态Token机制
- ✅ 所有Request模型移除session_id字段
- ✅ 前端完全移除cloudPortalSessionId变量
- ✅ 数据库新增Token相关字段（access_token, refresh_token等）
- ✅ 废弃`/api/cloud-portal-account/session`接口
- ✅ credentials接口增强，返回完整Token信息及有效性状态

**架构优势：**
- 支持水平扩展和多实例部署
- 减少中间状态，降低复杂度
- 符合RESTful和OAuth2最佳实践
- 提升代码可维护性和可读性

### v1.x (历史版本)

- 使用session_id进行会话管理
- 需要前端维护和传递会话标识
- 有状态设计，不支持多实例部署

---

**文档版本：** 2.0.0
**最后更新：** 2026-05-05
## 十一、拆分匹配接口

### 11.1 核查通行标识ID

**GET** `/api/split-match/verify-pass-id/`

核查通行标识ID是否在详单查询表中存在匹配记录。

**⚠️ 重要配置依赖：**

此接口**必须依赖** `config.ini` 配置文件中的 `[DETAIL_QUERY]` 节：

```ini
[DETAIL_QUERY]
table_name = 202005-202311_cf_1215
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pass_id | string | 是 | 待核查的通行标识ID |
| verify_type | string | 是 | 核查类型（如："核查通行标识"） |
| user_id | integer | 否 | 用户ID（可选） |
| username | string | 否 | 用户名（可选） |

响应（成功 - 找到记录）：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "exists": true,
    "match_count": 1,
    "records": [
      {
        "通行标识ID": "020000430101930023523020251211173306",
        "实际车辆车牌号码+颜色": "湘AMN845_7",
        "收费入口名称": "湖南龙塘站",
        "收费出口名称": "湖南涟源东站",
        "...": "其他字段"
      }
    ],
    "query_table": "202005-202311_cf_1215",
    "query_time": 15
  }
}
```

响应（成功 - 未找到记录）：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "exists": false,
    "match_count": 0,
    "records": [],
    "query_table": "202005-202311_cf_1215",
    "query_time": 12
  }
}
```

响应（配置缺失错误）：
```json
{
  "code": 400,
  "message": "未配置详单查询表名，请检查config.ini的[DETAIL_QUERY]节"
}
```

**说明：**
- 接口从 `config.ini` 的 `[DETAIL_QUERY]` 节读取 `table_name` 配置
- 只查询配置指定的单张详单表，不遍历其他月度表
- 返回值中包含 `query_table` 字段，显示实际查询的表名
- 使用参数化SQL查询，防止SQL注入
- 单次最多返回50条匹配记录

**配置变更说明：**
如需更换核查的数据源，只需修改 `config.ini`：
```ini
# 示例：更换为新的详单表
[DETAIL_QUERY]
table_name = 新的表名
```
修改后重启后端服务即可生效，无需修改代码。

### 11.2 拆分统计

**POST** `/api/split-match/split-statistics`

获取拆分统计信息（核查拆分='已拆'的记录数和拆分路段拆分金额总和）。

请求体：
```json
{
  "table_name": "202512",
  "record_id": "123"
}
```

---

## 十二、版本历史

### v2.1.0 (2026-05-07)

**新增功能：**
- ✅ 拆分匹配接口文档（第十一章）
- ✅ 核查通行标识ID接口详细说明
- ✅ config.ini配置依赖说明

**重要说明：**
- ⚠️ 核查接口依赖 `config.ini` 的 `[DETAIL_QUERY]` 节配置
- ⚠️ 必须正确配置 `table_name` 才能正常工作
- ⚠️ 配置变更后需重启后端服务

### v2.0.0 (2026-05-05)

**重大变更：**
- ✅ 完全移除session_id依赖，采用无状态Token机制
- ✅ 所有Request模型移除session_id字段
- ✅ 前端完全移除cloudPortalSessionId变量

**维护者：** 后端开发团队