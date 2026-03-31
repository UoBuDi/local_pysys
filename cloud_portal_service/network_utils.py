import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3.util.connection
import logging

logger = logging.getLogger(__name__)

_original_create_connection = None
_current_source_ip = None

def _patched_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, socket_options=None):
    global _current_source_ip
    
    if _current_source_ip:
        source_address = (_current_source_ip, 0)
    
    return _original_create_connection(
        address,
        timeout=timeout,
        source_address=source_address,
        socket_options=socket_options
    )

def patch_create_connection(source_ip):
    global _original_create_connection, _current_source_ip
    
    if _original_create_connection is None:
        _original_create_connection = urllib3.util.connection.create_connection
    
    _current_source_ip = source_ip
    urllib3.util.connection.create_connection = _patched_create_connection
    logger.info(f"已绑定网络请求源地址: {source_ip}")

def restore_create_connection():
    global _original_create_connection, _current_source_ip
    
    if _original_create_connection is not None:
        urllib3.util.connection.create_connection = _original_create_connection
        _current_source_ip = None
        logger.info("已恢复默认网络配置")

def create_portal_session(source_ip=None, retries=3):
    session = requests.Session()
    
    retry_strategy = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.trust_env = False
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    })
    
    if source_ip:
        patch_create_connection(source_ip)
    
    return session

def get_local_ips():
    local_ips = []
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        local_ips = [ip for ip in ip_list if not ip.startswith('127.')]
    except Exception as e:
        logger.error(f"获取本地IP失败: {e}")
    return local_ips

def check_network_connectivity(target_url, source_ip=None, timeout=5):
    try:
        session = create_portal_session(source_ip)
        response = session.get(target_url, timeout=timeout)
        return response.status_code == 200 or response.status_code < 500
    except Exception as e:
        logger.error(f"网络连通性检查失败: {e}")
        return False
