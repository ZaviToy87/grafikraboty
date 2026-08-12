# -*- coding: utf-8 -*-
"""
Тест GigaChat API
Проверка подключения и отправки запросов
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gigachat_api

print("=" * 60)
print(" GIGACHAT API - ПРОВЕРКА ПОДКЛЮЧЕНИЯ")
print("=" * 60)
print()

# 1. Получение токена
print("[1/3] Получение access token...")
token = gigachat_api.get_access_token()

if token:
    print(f"✅ ТОКЕН ПОЛУЧЕН")
    print(f"   Токен: {token[:40]}...")
    print(f"   Действует до: {gigachat_api._token_expiry}")
else:
    print("❌ ОШИБКА ПОЛУЧЕНИЯ ТОКЕНА")
    print("   Проверьте:")
    print("   - Authorization key в gigachat_api.py")
    print("   - Подключение к интернету")
    print("   - SSL сертификаты (корпоративный прокси?)")
    sys.exit(1)

print()

# 2. Получение списка моделей
print("[2/3] Получение списка моделей...")
models = gigachat_api.get_models()

if models:
    print(f"✅ ДОСТУПНЫЕ МОДЕЛИ ({len(models)}):")
    for model in models:
        print(f"   • {model}")
else:
    print("⚠️ Не удалось получить список моделей")
    print("   Продолжаем тест...")

print()

# 3. Тестовый запрос
print("[3/3] Тестовый запрос к GigaChat...")
response = gigachat_api.chat([
    {"role": "user", "content": "Привет! Как тебя зовут? Ответь кратко."}
])

if response:
    print(f"✅ ОТВЕТ ПОЛУЧЕН:")
    print(f"   {response}")
else:
    print("❌ ОШИБКА ПОЛУЧЕНИЯ ОТВЕТА")
    print("   Возможные причины:")
    print("   - Истёк срок действия токена (30 минут)")
    print("   - Проблемы с сетью")
    print("   - Лимиты API")

print()
print("=" * 60)
print(" ТЕСТ ЗАВЕРШЁН")
print("=" * 60)

print()
print("📋 ИНФОРМАЦИЯ:")
print("   • Токен действует 30 минут")
print("   • После истечения нужно запросить новый")
print("   • Для интеграции используйте gigachat_api.py")
print()
print("📁 ФАЙЛЫ:")
print("   • gigachat_api.py - API клиент")
print("   • .continue/config.json - конфиг для Continue")
print("   • test_gigachat.py - этот тест")
print()
