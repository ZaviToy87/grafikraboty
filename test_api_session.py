import requests

# Создаём сессию
session = requests.Session()

# 1. Загружаем страницу логина для получения куки
session.get('http://127.0.0.1:8080/login')
print('Cookies after /login:', session.cookies.get_dict())

# 2. Логинимся
login_data = {'username': 'admin', 'password': 'admin', 'channel': 'telegram'}
r = session.post('http://127.0.0.1:8080/login', json=login_data)
print('Login response:', r.json())
print('Cookies after login:', session.cookies.get_dict())

# 3. Пробуем получить график
r = session.get('http://127.0.0.1:8080/api/schedule?year=2026&month=3&user_id=1')
print('Schedule API:', r.status_code)
data = r.json()
print('Schedule data keys:', data.keys() if r.ok else 'ERROR')
if 'schedules' in data:
    print('Schedule entries:', len(data['schedules']))
