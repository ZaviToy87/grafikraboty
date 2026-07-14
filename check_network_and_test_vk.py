# -*- coding: utf-8 -*-
"""
Проверка сети и тест VK уведомлений
"""
import json
import os
import socket
import urllib.request
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("🔍 ПРОВЕРКА СЕТИ И VK УВЕДОМЛЕНИЙ")
print("=" * 60)
print()

# 1. Проверяем VK конфиг
print("📋 VK КОНФИГ:")
with open(os.path.join(BASE_DIR, 'vk_config.json')) as f:
    cfg = json.load(f)
print(f"  Токен: {cfg['service_token'][:20]}...")
print(f"  Group ID: {cfg['group_id']}")
print(f"  Admin VK ID: {cfg['admin_vk_id']}")
print(f"  Chat Peer ID: {cfg['chat_peer_id']}")
print()

# 2. Проверяем локальный IP
print("📍 ЛОКАЛЬНЫЙ IP:")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    local_ip = s.getsockname()[0]
    s.close()
    print(f"  IP: {local_ip}")
    print(f"  Ссылка: http://{local_ip}:8080")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")
    local_ip = "127.0.0.1"
print()

# 3. Проверяем внешний IP
print("🌍 ВНЕШНИЙ IP:")
try:
    req = urllib.request.Request('https://api.ipify.org')
    with urllib.request.urlopen(req, timeout=5) as r:
        public_ip = r.read().decode().strip()
    print(f"  IP: {public_ip}")
    print(f"  Ссылка: http://{public_ip}:8080")
except Exception as e:
    print(f"  ❌ Не удалось получить: {e}")
    public_ip = local_ip
print()

# 4. Проверяем порт 8080
print("🔌 ПРОВЕРКА ПОРТА 8080:")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    result = s.connect_ex(('127.0.0.1', 8080))
    s.close()
    if result == 0:
        print("  ✅ Порт 8080 открыт (сервер работает)")
    else:
        print("  ❌ Порт 8080 закрыт (сервер не запущен?)")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")
print()

# 5. Тест VK API
print("📤 ТЕСТ VK API:")
try:
    sys.path.insert(0, BASE_DIR)
    import vk_bot
    
    cfg = vk_bot.get_config()
    if cfg.get('service_token'):
        print(f"  ✅ Токен загружен: {cfg['service_token'][:20]}...")
        
        # Тест 1: Простое сообщение
        print("\n  📤 Тест 1: Отправка сообщения в чат группы...")
        result = vk_bot.send_message(
            peer_id=2000000001,
            message="🔄 Тест VK уведомлений от GrafikRaboty\n\nЕсли вы это видите — всё работает!"
        )
        if result:
            print("  ✅ Сообщение отправлено!")
        else:
            print("  ❌ Не удалось отправить")
        
        # Тест 2: Уведомление о запуске
        print("\n  📤 Тест 2: Отправка уведомления о запуске...")
        result = vk_bot.send_startup_notification(
            tunnel_url="тест",
            password=public_ip,
            link_local=f"http://{local_ip}:8080",
            local_ip=local_ip
        )
        if result:
            print("  ✅ Уведомление о запуске отправлено!")
        else:
            print("  ❌ Не удалось отправить")
        
        # Тест 3: Уведомление об открытии смены
        print("\n  📤 Тест 3: Отправка уведомления об открытии смены...")
        result = vk_bot.send_shift_notification('open', 'Тест', {
            'year': 2026, 'month': 7, 'day': 6, 'morning_cash': 10000
        })
        if result:
            print("  ✅ Уведомление о смене отправлено!")
        else:
            print("  ❌ Не удалось отправить")
    else:
        print("  ❌ Токен не загружен!")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)
print()
print("📱 Ссылки для доступа:")
print(f"  • Локально: http://{local_ip}:8080")
print(f"  • Внешний IP: http://{public_ip}:8080")
print()
print("⚠️  Если внешний IP не работает:")
print("  1. Проверьте проброс порта 8080 на роутере")
print("  2. Или используйте локальную ссылку в той же сети Wi-Fi")
