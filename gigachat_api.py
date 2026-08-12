# -*- coding: utf-8 -*-
"""
GigaChat API клиент для GrafikRaboty
Получение токенов и отправка запросов к GigaChat API
"""
import base64
import json
import urllib.request
import urllib.error
import ssl
import time
from datetime import datetime, timedelta

# Конфигурация Sber GigaChat API
GIGACHAT_CONFIG = {
    "client_id": "019d1174-9f1b-7e2e-a50d-ea3d21c51a04",
    "scope": "GIGACHAT_API_PERS",
    "auth_key": "MDE5ZDExNzQtOWYxYi03ZTJlLWE1MGQtZWEzZDIxYzUxYTA0OmNhZWY1MDEzLTNmZDUtNDY3MS1iMjkzLTRhM2I1NmRlNDhjZg==",
    "token_url": "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    "api_url": "https://gigachat.devices.sberbank.ru/api/v1",
    "rquid": "702a4dbb-305b-4fb3-afbb-216f068170cb"
}

# Глобальное состояние
_access_token = None
_token_expiry = None


def get_access_token(force_refresh=False):
    """
    Получить access token для GigaChat API.
    Токен действует 30 минут.
    
    Args:
        force_refresh: Принудительно обновить токен
        
    Returns:
        str: Access token или None при ошибке
    """
    global _access_token, _token_expiry
    
    # Если токен есть и не истёк - возвращаем его
    if _access_token and _token_expiry and not force_refresh:
        if datetime.now() < _token_expiry:
            print(f"[GigaChat] Используем кэшированный токен (действует до {_token_expiry.strftime('%H:%M:%S')})")
            return _access_token
    
    print("[GigaChat] Запрашиваем новый access token...")
    
    # Отключаем проверку SSL для корпоративных сетей
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        # Формируем запрос
        data = f"scope={GIGACHAT_CONFIG['scope']}"
        req = urllib.request.Request(
            GIGACHAT_CONFIG['token_url'],
            data=data.encode('utf-8'),
            method='POST'
        )
        
        # Добавляем заголовки
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Accept', 'application/json')
        req.add_header('RqUID', GIGACHAT_CONFIG['rquid'])
        req.add_header('Authorization', f'Basic {GIGACHAT_CONFIG["auth_key"]}')
        
        # Отправляем запрос
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        if 'access_token' in result:
            _access_token = result['access_token']
            # Токен действует 30 минут - устанавливаем expiry на 25 минут (с запасом)
            _token_expiry = datetime.now() + timedelta(minutes=25)
            print(f"[GigaChat] ✅ Токен получен (действует до {_token_expiry.strftime('%H:%M:%S')})")
            return _access_token
        else:
            print(f"[GigaChat] ❌ Ошибка: {result}")
            return None
            
    except Exception as e:
        print(f"[GigaChat] ❌ Ошибка получения токена: {e}")
        return None


def send_request(endpoint, payload, model="GigaChat:latest"):
    """
    Отправить запрос к GigaChat API.
    
    Args:
        endpoint: Endpoint API (например, '/chat/completions')
        payload: Данные запроса
        model: Модель для использования
        
    Returns:
        dict: Ответ API или None при ошибке
    """
    # Получаем токен
    token = get_access_token()
    if not token:
        return None
    
    # Отключаем проверку SSL
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        url = f"{GIGACHAT_CONFIG['api_url']}{endpoint}"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            method='POST'
        )
        
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        req.add_header('Authorization', f'Bearer {token}')
        
        with urllib.request.urlopen(req, timeout=60, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        return result
        
    except Exception as e:
        print(f"[GigaChat] ❌ Ошибка запроса: {e}")
        return None


def chat(messages, model="GigaChat:latest", temperature=0.7, max_tokens=2000):
    """
    Отправить сообщение в чат с GigaChat.
    
    Args:
        messages: Список сообщений в формате [{"role": "user", "content": "текст"}]
        model: Модель (GigaChat, GigaChat-Pro, и т.д.)
        temperature: Температура генерации (0-2)
        max_tokens: Максимальное количество токенов
        
    Returns:
        str: Ответ GigaChat или None при ошибке
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    result = send_request('/chat/completions', payload, model)
    
    if result and 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    
    return None


def get_models():
    """
    Получить список доступных моделей.
    
    Returns:
        list: Список моделей или None при ошибке
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    token = get_access_token()
    if not token:
        return None
    
    try:
        url = f"{GIGACHAT_CONFIG['api_url']}/models"
        req = urllib.request.Request(url, method='GET')
        req.add_header('Accept', 'application/json')
        req.add_header('Authorization', f'Bearer {token}')
        
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        if 'data' in result:
            return [model['id'] for model in result['data']]
        
        return None
        
    except Exception as e:
        print(f"[GigaChat] ❌ Ошибка получения списка моделей: {e}")
        return None


# Тестовый запуск
if __name__ == "__main__":
    print("=" * 60)
    print(" GIGACHAT API TEST")
    print("=" * 60)
    
    # Получаем токен
    token = get_access_token()
    if token:
        print(f"✅ Токен: {token[:50]}...")
        
        # Получаем список моделей
        print("\n📋 Доступные модели:")
        models = get_models()
        if models:
            for model in models:
                print(f"  - {model}")
        else:
            print("  Не удалось получить список моделей")
        
        # Тестовый запрос
        print("\n💬 Тестовый запрос:")
        response = chat([
            {"role": "user", "content": "Привет! Как тебя зовут?"}
        ])
        
        if response:
            print(f"  Ответ: {response}")
        else:
            print("  Не удалось получить ответ")
    else:
        print("❌ Не удалось получить токен")
    
    print("\n" + "=" * 60)
