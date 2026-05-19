import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class SourceAddressAdapter(HTTPAdapter):
    """
    源地址适配器 - 为每个Session独立绑定源IP地址
    解决全局状态污染问题，支持多会话并发
    """
    
    def __init__(self, source_address: Optional[str] = None, *args, **kwargs):
        self.source_address = (source_address, 0) if source_address else None
        super().__init__(*args, **kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        if self.source_address:
            kwargs['source_address'] = self.source_address
        return super().init_poolmanager(*args, **kwargs)
    
    def proxy_manager_for(self, proxy, **proxy_kwargs):
        if self.source_address:
            proxy_kwargs['source_address'] = self.source_address
        return super().proxy_manager_for(proxy, **proxy_kwargs)


class DefaultAdapter(HTTPAdapter):
    """
    默认适配器 - 不绑定源IP，使用系统默认路由
    """
    pass


def create_portal_session(source_ip: Optional[str] = None, retries: int = 3) -> requests.Session:
    """
    创建Portal会话
    
    Args:
        source_ip: 可选的源IP地址，用于绑定网络请求
        retries: 重试次数
        
    Returns:
        配置好的requests.Session对象
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    if source_ip:
        adapter = SourceAddressAdapter(source_ip, max_retries=retry_strategy)
        logger.info(f"创建会话并绑定源IP: {source_ip}")
    else:
        adapter = DefaultAdapter(max_retries=retry_strategy)
        logger.info("创建会话使用默认路由")
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.trust_env = False
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    })
    
    return session


def get_local_ips() -> List[str]:
    """
    获取本机所有非回环IP地址
    
    Returns:
        IP地址列表
    """
    local_ips = []
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        local_ips = [ip for ip in ip_list if not ip.startswith('127.')]
    except Exception as e:
        logger.error(f"获取本地IP失败: {e}")
    return local_ips


def validate_source_ip(source_ip: Optional[str]) -> bool:
    """
    验证源IP地址是否可用
    
    Args:
        source_ip: 要验证的IP地址
        
    Returns:
        IP地址是否在本机可用IP列表中
    """
    if not source_ip:
        return False
    local_ips = get_local_ips()
    is_valid = source_ip in local_ips
    if not is_valid:
        logger.warning(f"源IP {source_ip} 不在可用IP列表中: {local_ips}")
    return is_valid


def check_network_connectivity(target_url: str, source_ip: Optional[str] = None, timeout: int = 5) -> bool:
    """
    检查网络连通性
    
    Args:
        target_url: 目标URL
        source_ip: 可选的源IP地址
        timeout: 超时时间（秒）
        
    Returns:
        网络是否连通
    """
    try:
        session = create_portal_session(source_ip)
        response = session.get(target_url, timeout=timeout)
        is_connected = response.status_code == 200 or response.status_code < 500
        logger.info(f"网络连通性检查 - URL: {target_url}, 源IP: {source_ip or '默认'}, 状态: {'成功' if is_connected else '失败'}")
        return is_connected
    except Exception as e:
        logger.error(f"网络连通性检查失败: {e}")
        return False
