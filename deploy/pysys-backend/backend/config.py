import configparser
import os

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