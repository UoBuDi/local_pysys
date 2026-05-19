import requests
import hashlib
import json
import time
import logging
import base64
from typing import Dict, Optional, Any
from network_utils import create_portal_session, validate_source_ip, get_local_ips
from config import config, Timeouts

logger = logging.getLogger(__name__)


def parse_jwt_expiration(token: str) -> Optional[float]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning("[JWT解析] Token格式不正确，不是标准JWT格式")
            return None
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        exp = data.get('exp')
        if exp:
            logger.info(f"[JWT解析] Token过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exp))}")
        return exp
    except Exception as e:
        logger.error(f"[JWT解析] 解析Token失败: {e}")
        return None


class PortalClient:
    def __init__(self, source_ip: Optional[str] = None):
        self.source_ip = source_ip or config.ETHERNET2_IP
        
        logger.info(f"PortalClient初始化 - 配置源IP: {self.source_ip}")
        
        if validate_source_ip(self.source_ip):
            self.session = create_portal_session(self.source_ip)
            logger.info(f"成功绑定源IP: {self.source_ip}")
        else:
            logger.warning(f"源IP {self.source_ip} 不可用，使用默认路由")
            self.session = create_portal_session(None)
            self.source_ip = None
            
        self.owner_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.redirect_uri: Optional[str] = None
        self.user_info: Optional[Dict] = None
        self.token_expires_at: Optional[float] = None
        self.login_time: Optional[float] = None
        
        self.needs_relogin: bool = False
        self.relogin_reason: Optional[str] = None
    
    def set_owner(self, owner_id: str) -> None:
        """
        设置会话所有者
        
        Args:
            owner_id: 所有者标识（用户名或用户ID）
        """
        self.owner_id = owner_id
        logger.info(f"[会话绑定] 会话已绑定到用户: {owner_id}")
    
    def validate_owner(self, owner_id: str) -> bool:
        """
        验证请求者是否为会话所有者
        
        Args:
            owner_id: 待验证的所有者标识
            
        Returns:
            是否为会话所有者
        """
        if self.owner_id is None:
            return True
        return self.owner_id == owner_id
    
    def get_captcha(self) -> Dict[str, Any]:
        url = f"{config.PORTAL_BASE_URL}/captcha-server/api/captcha?{int(time.time() * 1000)}"
        
        logger.info(f"获取验证码 - URL: {url}, 源IP: {self.source_ip or '默认'}")
        
        total_start = time.time()
        
        try:
            dns_start = time.time()
            logger.info(f"[步骤1] 开始DNS解析: {config.PORTAL_BASE_URL}")
            
            response = self.session.get(
                url,
                timeout=Timeouts.CAPTCHA
            )
            
            dns_time = time.time() - dns_start
            total_time = time.time() - total_start
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[成功] 获取验证码完成 - DNS解析: {dns_time:.2f}s, 总耗时: {total_time:.2f}s, 状态码: {response.status_code}")
            return {
                'success': True,
                'img': data.get('img'),
                'uuid': data.get('uuid')
            }
        except requests.exceptions.Timeout:
            total_time = time.time() - total_start
            logger.error(f"[超时] 获取验证码超时 - 总耗时: {total_time:.2f}s (限制: {Timeouts.CAPTCHA}s), URL: {url}, 源IP: {self.source_ip}")
            return {
                'success': False,
                'error': f'获取验证码超时 ({total_time:.1f}s)，请检查网络连接或云门户服务器状态'
            }
        except requests.exceptions.ConnectionError as e:
            total_time = time.time() - total_start
            error_detail = str(e)
            logger.error(f"[连接失败] 获取验证码连接失败 - 总耗时: {total_time:.2f}s, URL: {url}, 源IP: {self.source_ip or '默认'}")
            logger.error(f"[错误详情] {error_detail}")
            
            if self.source_ip and ("Cannot assign requested address" in error_detail or "failed to bind" in error_detail.lower()):
                logger.error(f"[自动重试] 源IP {self.source_ip} 绑定失败，尝试使用默认路由重试...")
                self.session = create_portal_session(None)
                self.source_ip = None
                
                try:
                    retry_start = time.time()
                    retry_response = self.session.get(url, timeout=Timeouts.CAPTCHA)
                    retry_response.raise_for_status()
                    data = retry_response.json()
                    retry_time = time.time() - retry_start
                    logger.info(f"[重试成功] 使用默认路由重试成功 - 重试耗时: {retry_time:.2f}s")
                    return {
                        'success': True,
                        'img': data.get('img'),
                        'uuid': data.get('uuid')
                    }
                except Exception as retry_error:
                    retry_time = time.time() - retry_start
                    logger.error(f"[重试失败] 重试也失败 - 重试耗时: {retry_time:.2f}s, 错误: {retry_error}")
                    
            return {
                'success': False,
                'error': f'无法连接到云门户服务器 (源IP: {self.source_ip or "默认"}, 耗时: {total_time:.1f}s)'
            }
        except Exception as e:
            total_time = time.time() - total_start
            logger.error(f"[异常] 获取验证码异常 - 总耗时: {total_time:.2f}s", exc_info=True)
            return {
                'success': False,
                'error': f'获取验证码失败: {str(e)}'
            }
    
    def validate_captcha(self, captcha: str, uuid: str) -> Dict[str, Any]:
        url = f"{config.PORTAL_BASE_URL}/captcha-server/form/validate"
        params = {
            'captcha': captcha,
            'uuid': uuid
        }
        
        logger.info(f"[验证码校验] 开始 - URL: {url}")
        logger.info(f"[验证码校验] 参数 - captcha: {captcha}, uuid: {uuid}")
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=Timeouts.CAPTCHA
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"[验证码校验] 响应: {data}")
            
            if data.get('code') == '200':
                logger.info("[验证码校验] 成功")
                return {'success': True}
            else:
                error_msg = data.get('msg', '验证码错误')
                logger.warning(f"[验证码校验] 失败 - {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            logger.error(f"[验证码校验] 异常 - {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def login(self, username: str, password: str, captcha: str, uuid: str) -> Dict[str, Any]:
        logger.info(f"[登录] 开始 - 用户: {username}, 验证码: {captcha}, UUID: {uuid}")
        
        validate_result = self.validate_captcha(captcha, uuid)
        if not validate_result['success']:
            logger.warning(f"[登录] 验证码校验失败，终止登录")
            return validate_result
        
        password_md5 = hashlib.md5(password.encode()).hexdigest()
        
        url = f"{config.PORTAL_BASE_URL}/oauth-server/sso/ssoLogin"
        data = {
            'global_client': 'sso-web',
            'client_id': config.CLIENT_ID,
            'username': username,
            'password': password_md5,
            'redirect_uri': ''
        }
        
        logger.info(f"[登录] 请求URL: {url}")
        logger.info(f"[登录] 请求参数: global_client=sso-web, client_id={config.CLIENT_ID}, username={username}, password={password_md5}, redirect_uri=")
        
        try:
            response = self.session.post(
                url,
                data=data,
                timeout=Timeouts.LOGIN,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[登录] 响应: {result}")
            
            if result.get('code', {}).get('ok'):
                self.access_token = result['result']['global_access_token']
                self.refresh_token = result['result']['global_refresh_token']
                self.redirect_uri = result['result'].get('redirect_uri', '')
                self.login_time = time.time()
                
                jwt_exp = parse_jwt_expiration(self.access_token)
                if jwt_exp:
                    self.token_expires_at = jwt_exp
                    logger.info(f"[登录] 使用JWT实际过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(jwt_exp))}")
                else:
                    self.token_expires_at = self.login_time + 7200
                    logger.warning(f"[登录] JWT解析失败，使用默认2小时过期时间")
                
                self.needs_relogin = False
                self.relogin_reason = None
                
                self._fetch_user_info()
                
                logger.info(f"[登录] 用户 {username} 登录成功")
                
                return {
                    'success': True,
                    'user_info': self.user_info,
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'redirect_uri': self.redirect_uri
                }
            else:
                error_msg = result.get('code', {}).get('msg', '登录失败')
                logger.warning(f"[登录] 用户 {username} 登录失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except requests.exceptions.Timeout:
            logger.error("[登录] 请求超时")
            return {
                'success': False,
                'error': '登录请求超时，请检查网络连接'
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[登录] 连接失败: {e}")
            return {
                'success': False,
                'error': '无法连接到云门户服务器，请检查网络配置'
            }
        except Exception as e:
            logger.error(f"[登录] 异常: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'登录失败: {str(e)}'
            }
    
    def _fetch_user_info(self) -> None:
        if not self.access_token:
            return

        url = f"{config.PORTAL_HOME_URL}/gateway/user-server/user/getUserInfo.json"
        tenant_id = config.TENANT_ID

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{config.PORTAL_HOME_URL}/aiAuditWeb/index.html'
        }

        try:
            response = self.session.get(
                url,
                params={'tenantId': tenant_id},
                headers=headers,
                timeout=Timeouts.USER_INFO
            )
            response.raise_for_status()

            result = response.json()
            if result.get('code', {}).get('ok'):
                self.user_info = result.get('result', {}).get('user')
                logger.info(f"获取用户信息成功: {self.user_info.get('real_name', 'Unknown')}")
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")

    def _parse_redirect_uri_tokens(self, redirect_uri: str) -> Optional[Dict[str, str]]:
        """从 automaticLogin 返回的 redirect_uri URL 中提取 token 和 refresh_token"""
        if not redirect_uri:
            return None
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(redirect_uri)
            params = parse_qs(parsed.query)
            access_token = params.get('token', [None])[0]
            refresh_token = params.get('refresh_token', [None])[0]
            if not access_token:
                logger.warning("[Token解析] redirect_uri 中未找到 token 参数")
                return None
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except Exception as e:
            logger.error(f"[Token解析] redirect_uri 解析失败: {e}")
            return None

    def automatic_login(self) -> Dict[str, Any]:
        """使用 automaticLogin 接口进行令牌续期

        核心逻辑：
        - 使用 global_access_token 作为 Authorization 头（可过期）
        - 服务端校验 global_refresh_token 是否在有效期内（7天）
        - 有效则返回新的业务令牌（在 redirect_uri 的 query 参数中）
        - 无效则需重新走完整登录流程
        """
        if not self.access_token:
            return {'success': False, 'error': '无访问令牌'}

        url = f"{config.PORTAL_BASE_URL}/oauth-server/sso/automaticLogin"
        data = {
            'client_id': config.AUTO_LOGIN_CLIENT_ID,
            'redirect_uri': ''
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Authorization': self.access_token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Origin': 'http://sso.hngsetc.com',
            'Referer': f'http://sso.hngsetc.com/sso/skip.html?client_id={config.AUTO_LOGIN_CLIENT_ID}',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
        }

        try:
            logger.info(f"[自动登录] 请求URL: {url}, client_id={config.AUTO_LOGIN_CLIENT_ID}")
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                timeout=Timeouts.AUTO_LOGIN
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"[自动登录] 响应: code={result.get('code', {})}")

            if result.get('code', {}).get('ok'):
                redirect_uri = result['result'].get('redirect_uri', '')
                new_tokens = self._parse_redirect_uri_tokens(redirect_uri)

                if new_tokens and new_tokens['access_token']:
                    self.access_token = new_tokens['access_token']
                    if new_tokens['refresh_token']:
                        self.refresh_token = new_tokens['refresh_token']

                    jwt_exp = parse_jwt_expiration(self.access_token)
                    if jwt_exp:
                        self.token_expires_at = jwt_exp
                        logger.info(f"[自动登录] 续期成功 - JWT过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(jwt_exp))}")
                    else:
                        self.token_expires_at = time.time() + 7200
                        logger.warning("[自动登录] JWT解析失败，使用默认2小时过期时间")

                    self.needs_relogin = False
                    self.relogin_reason = None

                    self._fetch_user_info()
                    logger.info("[自动登录] 续期成功")
                    return {'success': True}
                else:
                    error_msg = "redirect_uri中未包含有效Token"
                    logger.warning(f"[自动登录] 续期响应异常: {error_msg}, redirect_uri={redirect_uri[:200]}")
                    self.needs_relogin = True
                    self.relogin_reason = error_msg
                    return {'success': False, 'error': error_msg}

            error_msg = result.get('code', {}).get('msg', '自动登录失败')
            self.needs_relogin = True
            self.relogin_reason = error_msg
            logger.warning(f"[自动登录] 失败: {error_msg}")
            return {'success': False, 'error': error_msg}

        except requests.exceptions.Timeout:
            logger.error("[自动登录] 请求超时")
            return {'success': False, 'error': '自动登录请求超时'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[自动登录] 连接失败: {e}")
            return {'success': False, 'error': f'无法连接到SSO服务器: {str(e)}'}
        except Exception as e:
            logger.error(f"[自动登录] 异常: {e}", exc_info=True)
            return {'success': False, 'error': f'自动登录异常: {str(e)}'}

    def check_login_status_by_api(self) -> Dict[str, Any]:
        """通过 getUserInfo 接口实时验证 Token 有效性和登录状态"""
        if not self.access_token:
            return {'logged_in': False, 'reason': '无访问令牌'}

        url = f"{config.PORTAL_HOME_URL}/gateway/user-server/user/getUserInfo.json"

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {self.access_token}',
            'DNT': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
            'Referer': f'{config.PORTAL_HOME_URL}/home/index.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
        }

        try:
            response = self.session.get(
                url,
                params={'tenantId': config.TENANT_ID},
                headers=headers,
                timeout=Timeouts.HEARTBEAT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('code', {}).get('code') == '0' and data.get('code', {}).get('ok'):
                    user = data.get('result', {}).get('user', {})
                    self.user_info = user
                    return {'logged_in': True, 'user_info': user}
                else:
                    return {'logged_in': False, 'reason': '用户信息接口返回异常'}

            elif response.status_code == 401:
                return {'logged_in': False, 'reason': 'Token已过期或无效'}

            else:
                return {'logged_in': False, 'reason': f'服务器返回HTTP {response.status_code}'}

        except requests.exceptions.Timeout:
            return {'logged_in': False, 'reason': '请求超时'}
        except requests.exceptions.ConnectionError as e:
            return {'logged_in': False, 'reason': f'连接失败: {str(e)}'}
        except Exception as e:
            return {'logged_in': False, 'reason': str(e)}

    def query_pass_data(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.access_token:
            return {
                'success': False,
                'error': '未登录'
            }
        
        if self.token_expires_at and time.time() > self.token_expires_at - config.TOKEN_REFRESH_THRESHOLD:
            logger.warning("Token即将过期或已过期")
            return {
                'success': False,
                'error': '登录已过期，请重新登录'
            }
        
        url = f"{config.PORTAL_HOME_URL}/gateway/portal-server/..."
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = self.session.post(
                url,
                headers=headers,
                json=query_params,
                timeout=Timeouts.QUERY
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"查询成功: {query_params}")
            return {
                'success': True,
                'data': result
            }
        except requests.exceptions.Timeout:
            logger.error("查询请求超时")
            return {
                'success': False,
                'error': '查询请求超时'
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"查询连接失败: {e}")
            return {
                'success': False,
                'error': '无法连接到云门户服务器'
            }
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {
                'success': False,
                'error': f'查询失败: {str(e)}'
            }
    
    def refresh_access_token(self) -> Dict[str, Any]:
        import warnings
        warnings.warn(
            "refresh_access_token() 已废弃，请使用 automatic_login() 替代",
            DeprecationWarning,
            stacklevel=2
        )
        
        if not self.refresh_token:
            return {
                'success': False,
                'error': '无刷新令牌'
            }
        
        url = f"{config.PORTAL_BASE_URL}/oauth-server/sso/refreshToken"
        data = {
            'refresh_token': self.refresh_token,
            'client_id': config.CLIENT_ID
        }
        
        try:
            response = self.session.post(
                url,
                data=data,
                timeout=Timeouts.REFRESH_TOKEN
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                self.access_token = result['result']['global_access_token']
                self.refresh_token = result['result'].get('global_refresh_token', self.refresh_token)
                
                jwt_exp = parse_jwt_expiration(self.access_token)
                if jwt_exp:
                    self.token_expires_at = jwt_exp
                    logger.info(f"[刷新Token] 使用JWT实际过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(jwt_exp))}")
                else:
                    self.token_expires_at = time.time() + 7200
                    logger.warning("[刷新Token] JWT解析失败，使用默认2小时过期时间")
                
                self.needs_relogin = False
                self.relogin_reason = None
                
                logger.info("Token刷新成功")
                return {'success': True}
            else:
                error_msg = result.get('code', {}).get('msg', '刷新失败')
                self.needs_relogin = True
                self.relogin_reason = f"Token刷新失败: {error_msg}"
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            logger.error(f"刷新Token失败: {e}")
            self.needs_relogin = True
            self.relogin_reason = f"Token刷新异常: {str(e)}"
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_and_refresh_token(self) -> bool:
        if not self.access_token or not self.refresh_token:
            logger.warning("[Token检查] 无Token或RefreshToken")
            self.needs_relogin = True
            self.relogin_reason = "无有效Token"
            return False
        
        if not self.token_expires_at:
            logger.warning("[Token检查] 无过期时间，尝试通过API验证状态")
            api_status = self.check_login_status_by_api()
            if not api_status['logged_in']:
                logger.info("[Token检查] API验证未通过，尝试自动续期...")
                renew_result = self.automatic_login()
                if renew_result['success']:
                    logger.info("[Token检查] 自动续期成功")
                    return True
                else:
                    logger.error(f"[Token检查] 自动续期也失败: {renew_result.get('error')}")
                    return False
            return True
        
        if time.time() > self.token_expires_at - config.TOKEN_REFRESH_THRESHOLD:
            logger.info("[Token检查] Token即将过期，开始自动续期...")
            result = self.automatic_login()
            if result['success']:
                logger.info("[Token检查] 自动续期成功")
                return True
            else:
                logger.error(f"[Token检查] 自动续期失败: {result.get('error')}")
                return False
        
        return True
    
    def keep_alive(self, use_twaudit: bool = True) -> Dict[str, Any]:
        if not self.access_token:
            return {
                'success': False,
                'error': '未登录，无法发送心跳'
            }
        
        if not self.check_and_refresh_token():
            return {
                'success': False,
                'error': 'Token已失效，请重新登录'
            }
        
        if use_twaudit:
            base_url = "http://twaudit.hngsetc.com"
            tenant_id = "fecbd87c54b34cd8863bd0640043660c"
        else:
            base_url = config.PORTAL_HOME_URL
            tenant_id = "1d68da3aa0a54f158fd6dab013a81d48"
        
        url = f"{base_url}/gateway/user-server/user/getUserInfo.json"
        
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'DNT': '1',
                'Authorization': f'Bearer {self.access_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49',
                'Referer': f'{base_url}/aiAuditWeb/index.html',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
            }
            
            response = self.session.get(
                url,
                params={'tenantId': tenant_id},
                headers=headers,
                timeout=Timeouts.HEARTBEAT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code', {}).get('code') == '0' or data.get('code', {}).get('ok'):
                    logger.info(f"[心跳] 连接保持成功 - 域名: {base_url}")
                    return {
                        'success': True,
                        'message': '连接保持成功'
                    }
            
            logger.warning(f"[心跳] 连接保持失败 - 状态码: {response.status_code}")
            return {
                'success': False,
                'error': f'心跳失败: HTTP {response.status_code}'
            }
            
        except requests.exceptions.Timeout:
            logger.error("[心跳] 请求超时")
            return {
                'success': False,
                'error': '心跳请求超时'
            }
        except Exception as e:
            logger.error(f"[心跳] 异常 - 错误: {e}")
            return {
                'success': False,
                'error': f'心跳异常: {str(e)}'
            }
    
    def logout(self) -> Dict[str, Any]:
        self.owner_id = None
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self.token_expires_at = None
        self.login_time = None
        self.needs_relogin = False
        self.relogin_reason = None
        
        logger.info("用户已登出")
        return {'success': True}
    
    def is_logged_in(self) -> bool:
        return self.access_token is not None and not self.needs_relogin
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'logged_in': self.is_logged_in(),
            'user_info': self.user_info,
            'login_time': self.login_time,
            'expires_at': self.token_expires_at,
            'needs_relogin': self.needs_relogin,
            'relogin_reason': self.relogin_reason,
            'owner_id': self.owner_id
        }
