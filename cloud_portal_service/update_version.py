import re
import os

config_file = 'config.py'

if os.path.exists(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'VERSION\s*=\s*"(\d+)\.(\d+)"', content)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        current = f'{major}.{minor:02d}'
        
        minor += 1
        if minor >= 100:
            minor = 0
            major += 1
        
        new_version = f'{major}.{minor:02d}'
        new_content = re.sub(r'VERSION\s*=\s*"\d+\.\d+"', f'VERSION = "{new_version}"', content)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f'Version updated: {current} -> {new_version}')
    else:
        print('Version not found in config.py')
else:
    print('config.py not found')
