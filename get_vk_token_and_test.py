# -*- coding: utf-8 -*-
"""
Скрипт для получения VK токена и тестирования отправки уведомлений
Группа: ВетГид (id=199112265)
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VK_CONFIG_FILE = os.path.join(BASE_DIR, 'vk_config.json')

print("=" * 60)
print("🔐 ПОЛУЧЕНИЕ VK ТОКЕНА ДЛЯ ГРУППЫ ВетГид")
print("=" * 60)
print()
print("ШАГ 1: Открой браузер и зайди по ссылке:")
print("  https://vk.com/club199112265")
print()
print("ШАГ 2: Перейди в:")
print("  Управление сообществом → Настройки → Работа с API")
print()
print("ШАГ 3: Создай ключ доступа (Create token):")
print("  - Выбери права: Сообщения (messages), Фото (photos), Документы (docs)")
print("  - Нажми 'Создать'")
print("  - Скопируй токен (начинается с vk1.a.)")
print()
print("ШАГ 4: Вставь токен сюда:")
print()

# Читаем текущий конфиг
config = {}
if os.path.exists(VK_CONFIG_FILE):
    try:
        with open(VK_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        pass

# Если конфиг пустой или с заглушкой
if not config.get('service_token') or config['service_token'] == 'ВАШ_ТОКЕН_СЮДА':
    token = input("  Вставь VK токен: ").strip()
    if token:
        config['service_token'] = token
        config['group_id'] = '199112265'
        config['admin_vk_id'] = '146411666'
        config['chat_peer_id'] = 2000000001
        config['api_version'] = '5.131'
        config['vk_user_map'] = {}
        
        with open(VK_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("✅ Токен сохранён в vk_config.json!")
    else:
        print("❌ Токен не введён")
        sys.exit(1)
else:
    print(f"✅ Токен уже есть: {config['service_token'][:10]}...")

print()
print("=" * 60)
print("📤 ТЕСТИРОВАНИЕ ОТПРАВКИ УВЕДОМЛЕНИЙ")
print("=" * 60)
print()

# Тестируем отправку
try:
    import vk_bot
    
    # Проверяем конфиг
    cfg = vk_bot.get_config()
    if cfg.get('service_token'):
        print(f"✅ Токен загружен: {cfg['service_token'][:10]}...")
        print(f"✅ Group ID: {cfg.get('group_id')}")
        print(f"✅ Admin VK ID: {cfg.get('admin_vk_id')}")
        print(f"✅ Chat Peer ID: {cfg.get('chat_peer_id')}")
        print()
        
        # Тест 1: Отправка уведомления о запуске
        print("📤 Тест 1: Отправка уведомления о запуске сервера...")
        result = vk_bot.send_startup_notification(
            tunnel_url="тест",
            password="тест",
            link_local="http://192.168.1.208:8080",
            local_ip="192.168.1.208"
        )
        if result:
            print("  ✅ Уведомление о запуске отправлено!")
        else:
            print("  ❌ Не удалось отправить уведомление о запуске")
        
        print()
        
        # Тест 2: Отправка уведомления об открытии смены
        print("📤 Тест 2: Отправка уведомления об открытии смены...")
        result = vk_bot.send_shift_notification('open', 'Тестовый сотрудник', {
            'year': 2026,
            'month': 7,
            'day': 6,
            'morning_cash': 10000
        })
        if result:
            print("  ✅ Уведомление об открытии смены отправлено!")
        else:
            print("  ❌ Не удалось отправить уведомление об открытии смены")
        
        print()
        
        # Тест 3: Отправка простого сообщения
        print("📤 Тест 3: Отправка тестового сообщения...")
        result = vk_bot.send_message(
            peer_id=2000000001,
            message="🔄 Тестовое сообщение от GrafikRaboty\n\nЕсли вы это видите — VK уведомления работают!"
        )
        if result:
            print("  ✅ Тестовое сообщение отправлено!")
        else:
            print("  ❌ Не удалось отправить тестовое сообщение")
            
    else:
        print("❌ Токен не загружен!")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("✅ Тестирование завершено")
print("=" * 60)
