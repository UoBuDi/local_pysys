import requests
import hashlib
import json
import time
import logging
from typing import Dict, Optional, Any
from network_utils import create_portal_session, restore_create_connection
from config import config

logger = logging.getLogger(__name__)

class PortalClient:
    def __init__(self, source_ip: Optional[str] = None):
        self.source_ip = source_ip or config.ETHERNET2_IP
        self.session = create_portal_session(self.source_ip)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_info: Optional[Dict] = None
        self.token_expires_at: Optional[float] = None
        self.login_time: Optional[float] = None
        
    def get_captcha(self) -> Dict[str, Any]:
        url = f"{config.PORTAL_BASE_URL}/captcha-server/api/captcha"
        
        try:
            response = self.session.get(
                url,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'img': data.get('img'),
                'uuid': data.get('uuid')
            }
        except requests.exceptions.Timeout:
            logger.error("获取验证码超时")
            return {
                'success': False,
                'error': '获取验证码超时，请检查网络连接'
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"获取验证码连接失败: {e}")
            return {
                'success': False,
                'error': '无法连接到云门户服务器，请检查网络配置'
            }
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
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
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == '200':
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': data.get('msg', '验证码错误')
                }
        except Exception as e:
            logger.error(f"验证验证码失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def login(self, username: str, password: str, captcha: str, uuid: str) -> Dict[str, Any]:
        validate_result = self.validate_captcha(captcha, uuid)
        if not validate_result['success']:
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
            
            if result.get('code', {}).get('ok'):
                self.access_token = result['result']['global_access_token']
                self.refresh_token = result['result']['global_refresh_token']
                self.login_time = time.time()
                self.token_expires_at = self.login_time + 86400
                
                self._fetch_user_info()
                
                logger.info(f"用户 {username} 登录成功")
                
                return {
                    'success': True,
                    'user_info': self.user_info
                }
            else:
                error_msg = result.get('code', {}).get('msg', '登录失败')
                logger.warning(f"用户 {username} 登录失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except requests.exceptions.Timeout:
            logger.error("登录请求超时")
            return {
                'success': False,
                'error': '登录请求超时，请检查网络连接'
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"登录连接失败: {e}")
            return {
                'success': False,
                'error': '无法连接到云门户服务器，请检查网络配置'
            }
        except Exception as e:
            logger.error(f"登录失败: {e}")
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
