import requests
import json
import sys

s = requests.Session()

# Логинимся через JSON API
r = s.post('http://127.0.0.1:8080/login', json={'username': 'admin', 'password': 'admin123', 'channel': 'telegram'})
print(f'Login status: {r.status_code}')
print(f'Login response: {r.text[:200]}')

data = r.json()
if data.get('status') == 'success':
    print('Login OK!')
elif data.get('status') == 'need_code':
    # Для админа нужна верификация - попробуем с обычным пользователем
    print('Admin needs verification, trying regular user...')
    r = s.post('http://127.0.0.1:8080/login', json={'username': 'user', 'password': 'user123', 'channel': 'telegram'})
    print(f'User login status: {r.status_code}')
    print(f'User login response: {r.text[:200]}')
else:
    print(f'Login failed: {data}')

# Проверяем daily-stats
r = s.get('http://127.0.0.1:8080/api/sync-1c/daily-stats?days=30')
print(f'\nDaily stats status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Keys: {list(data.keys())}')
    print(f'daily_data count: {len(data.get("daily_data", []))}')
    print(f'summary: {json.dumps(data.get("summary", {}), ensure_ascii=False, indent=2)}')
    if data.get('daily_data'):
        print(f'\nFirst day sample: {json.dumps(data["daily_data"][0], ensure_ascii=False, indent=2)}')
else:
    print(f'Error: {r.text[:500]}')
    sys.exit(1)
