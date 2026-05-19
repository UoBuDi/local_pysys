import requests
import json

base = 'http://localhost:8000'

login_resp = requests.post(f'{base}/api/login', json={'username': 'admin', 'password': 'admin123'})
login_data = login_resp.json()
print(f"Login: code={login_data.get('code')}, message={login_data.get('message')}")

token = login_data.get('data', {}).get('token', '')
headers = {'Authorization': f'Bearer {token}'}

menus_resp = requests.get(f'{base}/api/user/menus', headers=headers)
menus_data = menus_resp.json()
print(f"Menus: code={menus_data.get('code')}, count={len(menus_data.get('data', []))}")

perms_resp = requests.get(f'{base}/api/user/permissions', headers=headers)
perms_data = perms_resp.json()
print(f"Permissions: code={perms_data.get('code')}, count={len(perms_data.get('data', []))}")

def validate_routes(menus):
    errors = []
    def check(items, parent_path='', depth=0):
        for m in items:
            name = m.get('name', '')
            path = m.get('path', '')
            comp = m.get('component', '')
            redirect = m.get('redirect', '')
            children = m.get('children', [])
            meta = m.get('meta', {})

            full_path = f"{parent_path}/{path}".replace('//', '/') if parent_path else path

            if depth == 0 and not path.startswith('/'):
                errors.append(f"Top-level path must start with /: {name} path={path}")
            if depth > 0 and path.startswith('/'):
                errors.append(f"Child path must NOT start with /: {name} path={path}")
            if children and not redirect:
                errors.append(f"Parent missing redirect: {name}")
            if not name:
                errors.append(f"Missing name: path={path}")

            if children:
                check(children, full_path, depth + 1)

    check(menus)
    return errors

errors = validate_routes(menus_data.get('data', []))
if errors:
    print("\nVALIDATION ERRORS:")
    for e in errors:
        print(f"  - {e}")
else:
    print("\nAll routes validated successfully!")

print(f"\nToken preview: {token[:30]}...")
