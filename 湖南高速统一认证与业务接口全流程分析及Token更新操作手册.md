# 湖南高速统一认证与业务接口全流程分析及Token更新操作手册

## 文档说明

本文档基于真实抓包数据完整梳理**湖南高速SSO统一认证体系**的接口流程、鉴权逻辑、Token生命周期与Token更新方法，可直接用于开发、调试、自动化对接与问题排查。

---

## 一、整体流程概览

本次数据包完整覆盖：**自动登录失败 → 验证码校验 → 账号密码登录 → 门户跳转 → 获取用户信息 → 获取业务系统列表 → 查询全量收费站数据** 全链路。

核心机制：

- 统一认证中心：`api.hngsetc.com`

- 统一门户：`home.hngsetc.com`

- 鉴权方式：**JWT Bearer Token**

- 令牌结构：**短时效access_token + 长时效refresh_token**

---

## 二、数据包逐包详细解析

### 1. 自动登录（失败）

**接口**

```Plain Text

POST /oauth-server/sso/automaticLogin
```

**作用**

前端尝试使用本地缓存Token进行免密自动登录。

**结果**

- `401 Unauthorized`

- `offlined token`

**原因**

Token已过期、被下线、签名无效。

**触发动作**

前端退出自动登录，进入**账号密码+验证码**手动登录流程。

---

### 2. 获取验证码

**接口**

```Plain Text

GET /captcha-server/api/captcha
```

**作用**

获取登录验证码图片与唯一标识UUID。

**返回**

- img：base64编码的验证码图片

- uuid：验证码唯一ID

**用途**

防机器登录，必须校验通过才能提交账号密码。

---

### 3. 验证码校验

**接口**

```Plain Text

GET /captcha-server/form/validate?captcha=xxx&uuid=xxx
```

**作用**

提交用户输入的验证码进行校验。

**成功结果**

```JSON

{"msg":"验证码正确","code":"200"}
```

**关键节点**

验证码校验通过后，才允许发起登录请求。

---

### 4. 账号密码登录（核心：签发Token）

**接口**

```Plain Text

POST /oauth-server/sso/ssoLogin
```

**提交参数**

- global_client=sso-web

- client_id=门户应用ID

- username=账号

- password=MD5加密密码

- redirect_uri=空

**成功返回（最关键数据）**

```JSON

{
  "result": {
    "global_access_token": "短令牌（2小时）",
    "global_refresh_token": "长令牌（7天）",
    "redirect_uri": "门户跳转地址（带业务Token）"
  }
}
```

**核心意义**

- 登录成功，签发**全局双Token**

- 所有业务接口鉴权均依赖此Token

---

### 5. 统一门户首页加载

**接口**

```Plain Text

GET /home/index.html?token=xxx&refresh_token=xxx
```

**作用**

SSO认证成功后重定向到统一业务门户。

**携带**

门户专用access_token与refresh_token。

---

### 6. 获取当前登录用户信息

**接口**

```Plain Text

GET /gateway/user-server/user/getUserInfo.json
```

**作用**

使用Token获取当前登录人详细信息。

**返回关键字段**

- user_id、username、real_name、job_no、phone、id_card

- org_id、org_name（所属站点/部门）

- 账号状态、角色信息

**鉴权方式**

```Plain Text

Authorization: Bearer {门户Token}
```

---

### 7. 获取业务系统权限列表

**接口**

```Plain Text

POST /gateway/portal-server/functionsystem/getClientMap
```

**作用**

获取当前用户可访问的所有业务系统。

**关键系统（示例）**

- AI稽核系统

- 绿通车系统

- 收费特情车辆管理

- 门架管理系统

- 站级综合平台

**用途**

前端渲染“我的应用”菜单。

---

### 8. 获取全量收费站基础数据

**接口**

```Plain Text

GET /gateway/basicdata-server/api/orotollstation/v2/list
```

**作用**

获取湖南高速全量收费站标准数据。

**关键字段**

- tollstationid、tollstationname

- 桩号、经纬度、hex编码

- 所属路段、分公司、区域代码

- 启用状态、收费站类型

**用途**

业务系统下拉选择、地图展示、数据筛选、统计分析。

---

## 三、Token 体系与生命周期（必看）

### 1. Token 类型与用途

|Token名称|来源|有效期|用途|
|---|---|---|---|
|global_access_token|登录接口|2小时|全局接口鉴权|
|global_refresh_token|登录接口|7天|刷新短Token|
|业务子系统Token|登录返回|2小时|AI稽核等子系统专用|
### 2. 过期时间规则（从抓包解码）

- access_token：**2小时过期**

- refresh_token：**7天过期**

- 过期后接口返回：`401` / `offlined token`

### 3. Token 鉴权格式

所有业务请求必须携带：

```Plain Text

Authorization: Bearer {你的access_token}
```

---

## 四、Token 更新完整流程（可直接落地）

### 1. 何时需要更新

满足任一条件必须更新：

- 接口返回 `401 Unauthorized`

- 返回内容包含 `offlined token`

- 解码JWT后 `exp` ≤ 当前时间

---

### 2. 方法一：无感刷新（推荐，无需登录）

**适用场景**

access_token过期，但refresh_token仍有效（7天内）。

**刷新接口**

```Plain Text

POST https://api.hngsetc.com/oauth-server/sso/refreshToken
```

**请求头**

```Plain Text

Content-Type: application/x-www-form-urlencoded
Authorization: Bearer {旧access_token}
```

**请求体（表单）**

```Plain Text

client_id=sso-web
refresh_token={你的refresh_token}
```

**成功返回**

```JSON

{
  "code": { "code": "0", "msg": "操作成功" },
  "result": {
    "global_access_token": "新短Token",
    "global_refresh_token": "新长Token"
  }
}
```

**使用规则**

- 用新token替换所有请求头

- 保存新refresh_token供下次刷新

---

### 3. 方法二：重新登录（refresh_token也过期）

**适用场景**

refresh_token超过7天，或被强制作废。

**完整流程**

1. 获取验证码：`/captcha-server/api/captcha`

2. 校验验证码：`/captcha-server/form/validate`

3. 账号密码登录：`/oauth-server/sso/ssoLogin`

4. 直接获取全新双Token

---

### 4. 自动化刷新逻辑（代码可直接用）

```Plain Text

1. 发起业务请求
2. 若返回401/offlined token
3. 调用 /refreshToken 刷新
4. 替换新Token并重试业务请求
5. 若刷新也返回401 → 触发重新登录
```

---

## 五、常见问题与排查

### 1. 返回 offlined token

- Token过期

- 账号在别处登录

- 管理员强制注销

- 密码被修改

**处理**

优先刷新；失败则重新登录。

### 2. 验证码错误

- uuid与验证码不匹配

- 验证码超时过期

**处理**

重新获取验证码并校验。

### 3. 无业务系统权限

- Token正确但角色未授权

- client_id错误

- 账号未分配应用权限

**处理**

联系管理员分配权限。

---

## 六、总结

1. 湖南高速采用 **SSO统一认证 + JWT无状态鉴权**

2. 核心流程：**验证码 → 登录 → 签发双Token → 业务鉴权**

3. Token是唯一鉴权依据，**2小时过期，7天可刷新**

4. 刷新接口是保持在线最稳定方案

5. 全量收费站接口为业务系统核心基础数据


> （注：文档部分内容可能由 AI 生成）