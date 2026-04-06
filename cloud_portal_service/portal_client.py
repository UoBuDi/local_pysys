import requests
import hashlib
import json
import time
import logging
import socket
from typing import Dict, Optional, Any
from network_utils import create_portal_session, restore_create_connection, get_local_ips
from config import config

logger = logging.getLogger(__name__)

class PortalClient:
    def __init__(self, source_ip: Optional[str] = None):
        self.source_ip = source_ip or config.ETHERNET2_IP
        
        logger.info(f"PortalClient初始化 - 配置源IP: {self.source_ip}")
        
        if self._validate_source_ip(self.source_ip):
            self.session = create_portal_session(self.source_ip)
            logger.info(f"成功绑定源IP: {self.source_ip}")
        else:
            logger.warning(f"源IP {self.source_ip} 不可用，使用默认路由")
            self.session = create_portal_session(None)
            self.source_ip = None
            
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.redirect_uri: Optional[str] = None
        self.user_info: Optional[Dict] = None
        self.token_expires_at: Optional[float] = None
        self.login_time: Optional[float] = None
    
    def _validate_source_ip(self, ip: str) -> bool:
        if not ip:
            return False
            
        try:
            local_ips = get_local_ips()
            if ip not in local_ips:
                logger.warning(f"源IP {ip} 不在本地接口列表中: {local_ips}")
                return False
                
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind((ip, 0))
            test_socket.close()
            
            logger.info(f"源IP {ip} 验证通过")
            return True
            
        except OSError as e:
            logger.error(f"无法绑定源IP {ip}: {e}")
            return False
        except Exception as e:
            logger.error(f"验证源IP时出错: {e}")
            return False
        
    def get_captcha(self) -> Dict[str, Any]:
        url = f"{config.PORTAL_BASE_URL}/captcha-server/api/captcha"
        
        logger.info(f"获取验证码 - URL: {url}, 源IP: {self.source_ip or '默认'}")
        
        total_start = time.time()
        
        try:
            dns_start = time.time()
            logger.info(f"[步骤1] 开始DNS解析: {config.PORTAL_BASE_URL}")
            
            response = self.session.get(
                url,
                timeout=10
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
            logger.error(f"[超时] 获取验证码超时 - 总耗时: {total_time:.2f}s (限制: 10s), URL: {url}, 源IP: {self.source_ip}")
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
                restore_create_connection()
                self.session = create_portal_session(None)
                self.source_ip = None
                
                try:
                    retry_start = time.time()
                    retry_response = self.session.get(url, timeout=5)
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
                timeout=10
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
                timeout=15,
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
                self.token_expires_at = self.login_time + 86400
                
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
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                self.user_info = result.get('result', {}).get('user')
                logger.info(f"获取用户信息成功: {self.user_info.get('real_name', 'Unknown')}")
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
    
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
                timeout=30
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
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code', {}).get('ok'):
                self.access_token = result['result']['global_access_token']
                self.refresh_token = result['result'].get('global_refresh_token', self.refresh_token)
                self.token_expires_at = time.time() + 86400
                
                logger.info("Token刷新成功")
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': result.get('code', {}).get('msg', '刷新失败')
                }
        except Exception as e:
            logger.error(f"刷新Token失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_and_refresh_token(self) -> bool:
        """
        检查Token是否即将过期，如果是则自动刷新
        """
        if not self.access_token or not self.refresh_token:
            logger.warning("[Token检查] 无Token或RefreshToken")
            return False
        
        if not self.token_expires_at:
            logger.warning("[Token检查] 无过期时间")
            return False
        
        if time.time() > self.token_expires_at - config.TOKEN_REFRESH_THRESHOLD:
            logger.info("[Token检查] Token即将过期，开始刷新...")
            result = self.refresh_access_token()
            if result['success']:
                logger.info("[Token检查] Token刷新成功")
                return True
            else:
                logger.error(f"[Token检查] Token刷新失败: {result.get('error')}")
                return False
        
        return True
    
    def keep_alive(self, use_twaudit: bool = True) -> Dict[str, Any]:
        """
        发送心跳请求保持连接活跃
        使用getUserInfo接口验证会话有效性
        支持多域名心跳
        """
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
                timeout=10
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
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self.token_expires_at = None
        self.login_time = None
        
        logger.info("用户已登出")
        return {'success': True}
    
    def is_logged_in(self) -> bool:
        if not self.access_token:
            return False
        
        if self.token_expires_at and time.time() > self.token_expires_at:
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'logged_in': self.is_logged_in(),
            'user_info': self.user_info if self.is_logged_in() else None,
            'login_time': self.login_time,
            'expires_at': self.token_expires_at
        }
    
    def __del__(self):
        restore_create_connection()
