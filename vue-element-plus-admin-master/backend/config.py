import configparser
import os
import base64

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not os.path.exists(config_path):
        # 创建默认配置
        config['DATABASE'] = {
            'host': 'localhost',
            'port': '3306',
            'user': 'root',
            'password': 'password',
            'database': 'test'
        }
        config['ENCRYPTION'] = {
            'method': 'aes',  # rsa | aes
            'key_file': 'encryption.key'
        }
        with open(config_path, 'w') as f:
            config.write(f)
    else:
        config.read(config_path)
    return config

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    with open(config_path, 'w') as f:
        config.write(f)
    return True

def get_database_config(config, section='DATABASE'):
    return {
        'host': config.get(section, 'host', fallback='localhost'),
        'port': config.getint(section, 'port', fallback=3306),
        'user': config.get(section, 'user', fallback='root'),
        'password': config.get(section, 'password', fallback='password'),
        'database': config.get(section, 'database', fallback='test'),
        'charset': config.get(section, 'charset', fallback='utf8mb4')
    }

class EncryptionConfig:
    """加密配置类"""
    
    def __init__(self):
        self._config = None
        
    @property
    def method(self):
        if not self._config:
            return 'aes'  # 默认 AES
        return self._config.get('ENCRYPTION', 'method', fallback='aes')
    
    @property
    def key_file(self):
        if not self._config:
            return os.path.join(os.path.dirname(__file__), 'encryption.key')
        return self._config.get('ENCRYPTION', 'key_file', fallback=self.key_file)

def get_encryption_config():
    """获取加密配置"""
    config = load_config()
    enc_config = EncryptionConfig()
    
    # 加载密钥文件
    key_path = os.path.join(os.path.dirname(__file__), enc_config.key_file)
    if not os.path.exists(key_path):
        # 生成默认密钥 (32 字节，用于 AES-256)
        import secrets
        secret_bytes = secrets.token_bytes(32)
        with open(key_path, 'wb') as f:
            f.write(secret_bytes)
    
    try:
        with open(key_path, 'rb') as f:
            key_bytes = f.read()
        
        return {
            'method': enc_config.method,
            'key': base64.b64encode(key_bytes).decode('utf-8'),  # AES 密钥 Base64 编码
            'key_file': os.path.basename(key_path)
        }
    except Exception as e:
        print(f"[加密配置] 加载密钥失败：{e}")
        return {
            'method': enc_config.method,
            'key': base64.b64encode(os.urandom(32)).decode('utf-8'),  # 生成临时密钥
            'key_file': os.path.basename(enc_config.key_file)
        }

# AES 密钥 (Base64 编码的 32 字节随机值)
CLOUD_PORTAL_AES_KEY = ''

def get_cloud_portal_encrypt_key():
    """获取云门户加密密钥"""
    return EncryptionConfig().method, get_encryption_config()['key']