# GUI服务自动保持在线方案

## 一、现有架构分析

### 1. GUI服务现状

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GUI服务（cloud_portal_service）                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   SessionManager                    PortalClient                        │
│   ┌─────────────────┐              ┌─────────────────┐                 │
│   │ 心跳线程         │─────────────▶│ keep_alive()    │                 │
│   │ 重试机制         │              │ refresh_token() │                 │
│   │ 会话管理         │              │ login()         │                 │
│   └─────────────────┘              └─────────────────┘                 │
│          │                                   │                         │
│          │ 失败                              │ 失败                     │
│          ▼                                   ▼                         │
│   ┌─────────────────┐              ┌─────────────────┐                 │
│   │needs_relogin=True│              │needs_relogin=True│               │
│   │等待手动登录      │              │等待手动登录      │                 │
│   └─────────────────┘              └─────────────────┘                 │
│                                                                         │
│   ❌ 问题：没有自动重登录功能                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. 后端服务现状

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      后端服务（FastAPI）                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ✅ 已实现功能：                                                        │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │ 1. 账号密码存储（加密） - cloud_portal_accounts 表               │  │
│   │ 2. 自动登录接口 - /api/cloud-portal/auto-login                  │  │
│   │ 3. 获取凭证接口 - /api/cloud-portal-account/credentials         │  │
│   │ 4. 验证码识别 - ddddocr                                         │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   自动登录流程：                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │获取验证码│───▶│ddddocr识别│───▶│成功？    │───▶│自动登录  │        │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘        │
│                          │              │                              │
│                          │ 失败         │                              │
│                          ▼              ▼                              │
│                   ┌──────────┐    ┌──────────┐                        │
│                   │返回验证码│    │返回Token │                        │
│                   │供手动输入│    │登录成功  │                        │
│                   └──────────┘    └──────────┘                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 二、整合方案设计

### 方案概述

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      自动保持在线整合方案                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   GUI服务                           后端服务                            │
│   ┌─────────────────┐              ┌─────────────────┐                 │
│   │ SessionManager  │              │ FastAPI         │                 │
│   │                 │              │                 │                 │
│   │ 心跳失败        │              │ 自动登录接口    │                 │
│   │ Token过期       │─────────────▶│ ddddocr识别     │                 │
│   │ needs_relogin   │              │ 账号密码存储    │                 │
│   │       │         │              │                 │                 │
│   │       ▼         │◀─────────────│ 返回结果        │                 │
│   │ 自动重登录      │              │                 │                 │
│   │ 更新会话        │              │                 │                 │
│   └─────────────────┘              └─────────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 详细流程图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   心跳线程   │    │SessionManager│    │   后端API   │    │  PortalClient│
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       │ 1.发送心跳       │                  │                  │
       │─────────────────────────────────────────────────────────>│
       │                  │                  │                  │
       │                  │                  │     失败/Token过期│
       │<─────────────────────────────────────────────────────────│
       │                  │                  │                  │
       │ 2.设置needs_relogin=true           │                  │
       │─────────────────>│                  │                  │
       │                  │                  │                  │
       │                  │ 3.获取账号凭证   │                  │
       │                  │─────────────────>│                  │
       │                  │                  │                  │
       │                  │ 4.返回用户名密码 │                  │
       │                  │<─────────────────│                  │
       │                  │                  │                  │
       │                  │ 5.调用自动登录   │                  │
       │                  │─────────────────>│                  │
       │                  │                  │                  │
       │                  │                  │ 6.获取验证码     │
       │                  │                  │─────────────────────────────>│
       │                  │                  │                  │          │
       │                  │                  │     7.返回验证码│          │
       │                  │                  │<─────────────────────────────│
       │                  │                  │                  │          │
       │                  │                  │ 8.ddddocr识别   │          │
       │                  │                  │────────┐         │          │
       │                  │                  │        │         │          │
       │                  │                  │◀───────┘         │          │
       │                  │                  │                  │          │
       │                  │                  │ 9.自动提交登录   │          │
       │                  │                  │─────────────────────────────>│
       │                  │                  │                  │          │
       │                  │                  │    10.返回Token  │          │
       │                  │                  │<─────────────────────────────│
       │                  │                  │                  │          │
       │                  │ 11.返回登录结果  │                  │          │
       │                  │<─────────────────│                  │          │
       │                  │                  │                  │          │
       │                  │ 12.更新会话Token │                  │          │
       │                  │─────────────────────────────────────────────────>│
       │                  │                  │                  │          │
       │ 13.重置needs_relogin=false         │                  │          │
       │<─────────────────│                  │                  │          │
       │                  │                  │                  │          │
```

## 三、实施步骤

### 步骤1：修改GUI服务配置

在 `config.py` 中添加后端API地址配置：

```python
DEFAULT_CONFIG = {
    # ... 现有配置 ...
    "backend": {
        "host": "172.32.48.254",
        "port": 8000,
        "auto_relogin_enabled": True,  # 启用自动重登录
        "auto_relogin_user_id": 1      # 默认用户ID（用于获取凭证）
    }
}
```

### 步骤2：修改PortalClient添加自动重登录方法

在 `portal_client.py` 中添加：

```python
def auto_relogin(self, backend_url: str, user_id: int) -> Dict[str, Any]:
    """
    通过后端自动登录接口重新登录
    
    Args:
        backend_url: 后端服务地址
        user_id: 用户ID
        
    Returns:
        登录结果
    """
    import requests as req
    
    try:
        # 1. 获取保存的账号凭证
        credentials_url = f"{backend_url}/api/cloud-portal-account/credentials"
        # 注意：这里需要认证，可以使用内部认证或跳过认证
        
        # 2. 调用自动登录接口
        auto_login_url = f"{backend_url}/api/cloud-portal/auto-login"
        response = req.post(
            auto_login_url,
            json={
                'username': username,
                'password': password
            },
            timeout=60
        )
        
        result = response.json()
        
        if result.get('code') == 200:
            # 自动登录成功
            data = result.get('data', {})
            self.access_token = data.get('access_token')
            self.refresh_token = data.get('refresh_token')
            self.user_info = data.get('user_info')
            self.login_time = time.time()
            self.token_expires_at = self.login_time + 86400
            
            self.needs_relogin = False
            self.relogin_reason = None
            
            logger.info(f"[自动重登录] 成功 - 用户: {username}")
            return {'success': True}
            
        elif result.get('code') == 201:
            # 需要手动输入验证码
            logger.warning("[自动重登录] 验证码识别失败，需要手动输入")
            return {
                'success': False,
                'need_manual_captcha': True,
                'captcha_img': result.get('data', {}).get('img'),
                'uuid': result.get('data', {}).get('uuid'),
                'session_id': result.get('data', {}).get('session_id')
            }
        else:
            logger.error(f"[自动重登录] 失败 - {result.get('message')}")
            return {
                'success': False,
                'error': result.get('message')
            }
            
    except Exception as e:
        logger.error(f"[自动重登录] 异常 - {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

### 步骤3：修改SessionManager添加自动重登录逻辑

在 `session_manager.py` 中修改心跳循环：

```python
def _keep_alive_loop(self):
    while self.running:
        try:
            if self.is_idle() and self.sessions:
                for session_id, client in list(self.sessions.items()):
                    if client.access_token:
                        # 发送心跳
                        result = self._keep_alive_with_retry(session_id, client)
                        
                        if not result['success']:
                            # 心跳失败，检查是否需要自动重登录
                            if client.needs_relogin and config.AUTO_RELOGIN_ENABLED:
                                logger.info(f"[自动重登录] 会话 {session_id} 开始自动重登录...")
                                
                                relogin_result = client.auto_relogin(
                                    backend_url=config.BACKEND_URL,
                                    user_id=config.AUTO_RELOGIN_USER_ID
                                )
                                
                                if relogin_result['success']:
                                    logger.info(f"[自动重登录] 会话 {session_id} 重登录成功")
                                    self.consecutive_failures[session_id] = 0
                                elif relogin_result.get('need_manual_captcha'):
                                    logger.warning(f"[自动重登录] 会话 {session_id} 需要手动输入验证码")
                                    # 通知前端需要手动输入验证码
                                    self._notify_manual_captcha_needed(
                                        session_id,
                                        relogin_result.get('captcha_img'),
                                        relogin_result.get('uuid'),
                                        relogin_result.get('session_id')
                                    )
                                else:
                                    logger.error(f"[自动重登录] 会话 {session_id} 重登录失败")
                        else:
                            self.heartbeat_success_count += 1
                            self.consecutive_failures[session_id] = 0
                            
        except Exception as e:
            logger.error(f"[心跳循环] 异常 - 错误: {e}")
            time.sleep(60)
```

### 步骤4：添加前端通知机制

在 `api_server.py` 中添加WebSocket或轮询接口：

```python
# 存储需要手动输入验证码的会话
manual_captcha_sessions = {}

@app.route('/api/portal/manual-captcha/check', methods=['GET'])
def check_manual_captcha():
    """检查是否有会话需要手动输入验证码"""
    session_id = request.args.get('session_id')
    
    if session_id and session_id in manual_captcha_sessions:
        data = manual_captcha_sessions.pop(session_id)
        return jsonify({
            'code': 200,
            'need_captcha': True,
            'data': data
        })
    
    return jsonify({
        'code': 200,
        'need_captcha': False
    })
```

## 四、关键问题与解决方案

| 问题 | 解决方案 |
|------|----------|
| **后端API认证** | 方案A：使用内部服务认证（推荐）<br>方案B：跳过认证（仅限内部调用）<br>方案C：使用服务账号Token |
| **验证码识别失败** | 通知前端弹出验证码输入框，用户手动输入 |
| **多用户场景** | 每个会话关联用户ID，自动重登录时使用对应用户凭证 |
| **并发安全** | 使用线程锁保护会话状态更新 |
| **失败重试** | 自动重登录失败后，等待下次心跳周期再尝试 |

## 五、配置建议

```python
# service_config.json
{
    "auto_relogin": {
        "enabled": true,
        "max_attempts": 3,
        "retry_interval": 300,
        "notify_frontend": true
    },
    "backend": {
        "host": "172.32.48.254",
        "port": 8000,
        "internal_token": "your-internal-token"
    }
}
```

## 六、优缺点分析

| 项目 | 说明 |
|------|------|
| **优点** | 1. 自动保持在线，无需用户干预<br>2. 利用现有自动登录功能，开发成本低<br>3. 验证码识别失败时有降级方案<br>4. 提高系统可用性 |
| **缺点** | 1. 需要GUI服务与后端服务保持通信<br>2. 验证码识别率非100%<br>3. 增加系统复杂度 |
| **风险** | 1. 账号密码存储安全（已加密）<br>2. 自动登录可能触发安全策略<br>3. 需要处理网络异常情况 |

## 七、实施建议

1. **优先级**：高 - 解决Token过期导致服务中断的问题
2. **实施顺序**：
   - 第一步：修改配置，添加后端地址
   - 第二步：修改PortalClient，添加自动重登录方法
   - 第三步：修改SessionManager，集成自动重登录逻辑
   - 第四步：添加前端通知机制
   - 第五步：测试验证

## 八、相关文件

- GUI服务配置：`cloud_portal_service/config.py`
- 会话管理：`cloud_portal_service/session_manager.py`
- Portal客户端：`cloud_portal_service/portal_client.py`
- API服务：`cloud_portal_service/api_server.py`
- 后端自动登录：`vue-element-plus-admin-master/backend/main.py`
- 验证码识别：`vue-element-plus-admin-master/backend/captcha_ocr.py`
