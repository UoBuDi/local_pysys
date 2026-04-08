import json
import os
import sys

VERSION = "1.75"

def get_base_path():
    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        if hasattr(sys, 'argv') and sys.argv:
            exe_path = os.path.abspath(sys.argv[0])
            if os.path.exists(exe_path):
                return os.path.dirname(exe_path)
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(get_base_path(), 'service_config.json')

DEFAULT_CONFIG = {
    "gui_host": "172.32.48.239",
    "gui_port": 9000,
    "auto_start": False,
    "portal_base_url": "http://api.hngsetc.com",
    "portal_sso_url": "http://sso.hngsetc.com",
    "portal_home_url": "http://home.hngsetc.com",
    "client_id": "7d569fe611e44189b19dc286b3f0a8a6",
    "session_timeout": 3600,
    "token_refresh_threshold": 300,
    "log_level": "INFO",
    "network": {
        "ethernet_ip": "172.32.48.239",
        "ethernet2_ip": "10.143.164.29",
        "use_ethernet2_for_portal": True
    },
    "backend": {
        "host": "172.32.48.254",
        "port": 8000
    }
}

class Config:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save_config()
    
    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key, default=None):
        return self._config.get(key, default)
    
    def set(self, key, value):
        self._config[key] = value
        self.save_config()
    
    @property
    def GUI_HOST(self):
        return self._config.get('gui_host', DEFAULT_CONFIG['gui_host'])
    
    @property
    def GUI_PORT(self):
        return self._config.get('gui_port', DEFAULT_CONFIG['gui_port'])
    
    @property
    def AUTO_START(self):
        return self._config.get('auto_start', DEFAULT_CONFIG['auto_start'])
    
    @property
    def PORTAL_BASE_URL(self):
        return self._config.get('portal_base_url', DEFAULT_CONFIG['portal_base_url'])
    
    @property
    def PORTAL_SSO_URL(self):
        return self._config.get('portal_sso_url', DEFAULT_CONFIG['portal_sso_url'])
    
    @property
    def PORTAL_HOME_URL(self):
        return self._config.get('portal_home_url', DEFAULT_CONFIG['portal_home_url'])
    
    @property
    def CLIENT_ID(self):
        return self._config.get('client_id', DEFAULT_CONFIG['client_id'])
    
    @property
    def SESSION_TIMEOUT(self):
        return self._config.get('session_timeout', DEFAULT_CONFIG['session_timeout'])
    
    @property
    def TOKEN_REFRESH_THRESHOLD(self):
        return self._config.get('token_refresh_threshold', DEFAULT_CONFIG['token_refresh_threshold'])
    
    @property
    def LOG_LEVEL(self):
        return self._config.get('log_level', DEFAULT_CONFIG['log_level'])
    
    @property
    def NETWORK(self):
        return self._config.get('network', DEFAULT_CONFIG['network'])
    
    @property
    def ETHERNET_IP(self):
        return self.NETWORK.get('ethernet_ip', DEFAULT_CONFIG['network']['ethernet_ip'])
    
    @property
    def ETHERNET2_IP(self):
        return self.NETWORK.get('ethernet2_ip', DEFAULT_CONFIG['network']['ethernet2_ip'])
    
    @property
    def BACKEND(self):
        return self._config.get('backend', DEFAULT_CONFIG['backend'])
    
    @property
    def BACKEND_HOST(self):
        return self.BACKEND.get('host', DEFAULT_CONFIG['backend']['host'])
    
    @property
    def BACKEND_PORT(self):
        return self.BACKEND.get('port', DEFAULT_CONFIG['backend']['port'])
    
    @property
    def BACKEND_URL(self):
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"
    
    @property
    def VERSION(self):
        return VERSION

config = Config()
