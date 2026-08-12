import requests

session = requests.Session()

# Логин через Telegram
login = session.post('http://127.0.0.1:8080/login', json={'username': 'admin', 'password': 'admin', 'channel': 'telegram'})
print('Login:', login.json())
print('Cookies:', session.cookies.get_dict())

if login.json().get('status') == 'need_code':
    token = login.json().get('temp_token')
    print(f'Temp token: {token}')
    
    # Вводим любой код (для теста)
    verify = session.post('http://127.0.0.1:8080/login/verify-telegram', 
                          json={'temp_token': token, 'code': '0000'})
    print('Verify:', verify.json())
    print('Cookies after verify:', session.cookies.get_dict())
    
    # Пробуем API
    if verify.json().get('status') == 'success':
        api = session.get('http://127.0.0.1:8080/api/schedule?year=2026&month=3&user_id=1')
        print('Schedule API:', api.status_code)
        if api.ok:
            data = api.json()
            print('Schedule entries:', len(data.get('schedules', [])))
        else:
            print('Schedule error:', api.json())
