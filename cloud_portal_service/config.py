import json
import os
import sys

VERSION = "1.78"

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
    "auto_login_client_id": "c3a92b6963d84a3e827f3d79119a27a5",
    "tenant_id": "1d68da3aa0a54f158fd6dab013a81d48",
    "session_timeout": 3600,
    "token_refresh_threshold": 300,
    "auto_renew_interval": 3600,
    # TODO [安全策略-预留] 登录天数阈值强制重认证功能
    # 设计意图：用户登录超过N天后，即使Token有效也要求重新登录以增强安全性
    # 业务场景：符合安全审计要求、降低长期Token被盗用风险、定期重新认证最佳实践
    # 当前状态：基础设施已完备（login_time/needs_relogin/relogin_reason），核心判断逻辑待实现
    # 实现位置：portal_client.py - PortalClient类（需添加_check_login_age_threshold方法）
    # 集成点建议：
    #   - is_logged_in() [P0] 状态查询入口
    #   - query_pass_data() [P0] 核心业务操作前
    #   - check_and_refresh_token() [P1] Token刷新前
    #   - SessionManager心跳任务 [P2] 主动检测通知
    # 相关配置项：session_timeout(秒级Token过期)、token_refresh_threshold(刷新阈值)
    # 参考标准：OWASP Session Management Verification Checklist
    # 类似系统：GitHub(30天)、AWS Console(12小时)、Linux sudo(15分钟可配)
    # 预估工作量：3小时（含测试），核心逻辑约30分钟
    # 优先级：P2（可选优化），如需安全合规可提升至P1
    # 决策记录：
    #   日期: 2026-05-18 | 决策: 保留配置并标注 | 原因: 平衡灵活性与清晰度
    #   负责人: 用户确认 | 下次评估: 有安全需求时激活实现
    "relogin_threshold_days": 6,
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

class Timeouts:
    CAPTCHA = 30
    LOGIN = 60
    USER_INFO = 30
    QUERY = 30
    REFRESH_TOKEN = 30
    AUTO_LOGIN = 15
    HEARTBEAT = 10

class Limits:
    REQUEST_LOG_SIZE = 100
    REQUEST_INFO_SIZE = 50
    IDLE_THRESHOLD = 300
    ALERT_THRESHOLD = 3
    MAX_RETRY_COUNT = 3
    RETRY_INTERVAL = 5
    RETRY_BACKOFF = 2
    CAPTCHA_TTL = 300
    CAPTCHA_RATE_LIMIT = 10
    CAPTCHA_RATE_PERIOD = 60

class Intervals:
    HEARTBEAT_MIN = 50
    HEARTBEAT_MAX = 70
    CLEANUP = 60

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
    def AUTO_LOGIN_CLIENT_ID(self):
        return self._config.get('auto_login_client_id', DEFAULT_CONFIG['auto_login_client_id'])

    @property
    def TENANT_ID(self):
        return self._config.get('tenant_id', DEFAULT_CONFIG['tenant_id'])

    @property
    def SESSION_TIMEOUT(self):
        return self._config.get('session_timeout', DEFAULT_CONFIG['session_timeout'])
    
    @property
    def TOKEN_REFRESH_THRESHOLD(self):
        return self._config.get('token_refresh_threshold', DEFAULT_CONFIG['token_refresh_threshold'])

    @property
    def AUTO_RENEW_INTERVAL(self):
        return self._config.get('auto_renew_interval', DEFAULT_CONFIG['auto_renew_interval'])

    @property
    def RELOGIN_THRESHOLD_DAYS(self):
        # [预留配置] 登录天数阈值 - 当前仅提供访问接口，业务逻辑待实现
        # 详见 DEFAULT_CONFIG 中 relogin_threshold_days 的 TODO 注释
        return self._config.get('relogin_threshold_days', DEFAULT_CONFIG['relogin_threshold_days'])

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
