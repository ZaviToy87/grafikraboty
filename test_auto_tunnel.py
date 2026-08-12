# -*- coding: utf-8 -*-
"""
Тест автозапуска туннеля
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print("=" * 70)
print(" ТЕСТ АВТОЗАПУСКА ТУННЕЛЯ")
print("=" * 70)
print()

# Проверяем импорт
print("1️⃣ Проверка импорта auto_tunnel_launcher:")
try:
    import auto_tunnel_launcher
    print("  ✅ Модуль импортирован")
except Exception as e:
    print(f"  ❌ Ошибка импорта: {e}")
    sys.exit(1)

print()

# Проверяем функции
print("2️⃣ Проверка функций:")
functions_to_check = [
    'start_auto_tunnel',
    'run_tunnel',
    'send_tunnel_notification',
    'save_tunnel_info',
    'check_tunnel_health',
    'get_local_ip',
    'get_public_ip',
    'find_node'
]

for func_name in functions_to_check:
    if hasattr(auto_tunnel_launcher, func_name):
        print(f"  ✅ {func_name}")
    else:
        print(f"  ❌ {func_name} - НЕ НАЙДЕНА")

print()

# Проверяем Node.js
print("3️⃣ Проверка Node.js:")
node_dir = auto_tunnel_launcher.find_node()
if node_dir:
    print(f"  ✅ Node.js найден: {node_dir}")
    
    # Проверяем lt
    import os
    lt_path = os.path.join(node_dir, 'lt')
    if os.path.exists(lt_path):
        print(f"  ✅ lt найден: {lt_path}")
    else:
        print(f"  ⚠️ lt не найден в {lt_path}")
        print("     Установи: npm install -g localtunnel")
else:
    print("  ❌ Node.js не найден")
    print("     Установи Node.js с https://nodejs.org/")

print()

# Проверяем IP
print("4️⃣ Проверка IP:")
local_ip = auto_tunnel_launcher.get_local_ip()
public_ip = auto_tunnel_launcher.get_public_ip()

print(f"  ✅ Локальный IP: {local_ip}")
print(f"  ✅ Внешний IP: {public_ip}")

print()

# Проверяем VK конфигурацию
print("5️⃣ Проверка VK конфигурации:")
config = auto_tunnel_launcher.load_vk_config()

if config:
    print(f"  ✅ Токен: {'настроен' if config.get('service_token') else '❌ не настроен'}")
    print(f"  ✅ Admin VK ID: {config.get('admin_vk_id')}")
    print(f"  ✅ Chat Peer ID: {config.get('chat_peer_id')}")
else:
    print("  ❌ VK конфигурация не загружена")

print()

# Проверяем tunnel_info.json
print("6️⃣ Проверка tunnel_info.json:")
import json

tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
if os.path.exists(tunnel_info_path):
    with open(tunnel_info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)
    
    print(f"  ✅ URL: {info.get('tunnel_url', 'не указан')}")
    print(f"  ✅ Пароль: {info.get('password', 'не указан')}")
    print(f"  ✅ Local IP: {info.get('local_ip', 'не указан')}")
    print(f"  ✅ Public IP: {info.get('public_ip', 'не указан')}")
    print(f"  ✅ Запущен: {info.get('started_at', 'не указан')}")
else:
    print("  ⚠️ tunnel_info.json не найден")
    print("     Будет создан при запуске туннеля")

print()

# Проверяем сервер
print("7️⃣ Проверка сервера:")
import socket

server_ok = False
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex(('127.0.0.1', 8080))
    sock.close()
    server_ok = (result == 0)
except:
    pass

if server_ok:
    print("  ✅ Сервер запущен на порту 8080")
else:
    print("  ⚠️ Сервер не запущен")
    print("     Запусти: python launcher_with_vk.py")

print()

# Проверяем процесс туннеля
print("8️⃣ Проверка процесса туннеля:")
import subprocess

try:
    result = subprocess.run(['tasklist', '/FI', 'WINDOWTITLE eq Localtunnel*'], 
                          capture_output=True, text=True, timeout=5)
    if 'node.exe' in result.stdout:
        print("  ✅ Процесс туннеля запущен")
    else:
        print("  ⚠️ Процесс туннеля не найден")
except Exception as e:
    print(f"  ⚠️ Ошибка проверки: {e}")

print()
print("=" * 70)
print(" РЕЗУЛЬТАТ ТЕСТА")
print("=" * 70)
print()

if server_ok and node_dir:
    print("✅ ВСЁ ГОТОВО К ЗАПУСКУ!")
    print()
    print("📝 Для запуска сервера с автозапуском туннеля:")
    print("   python launcher_with_vk.py")
    print()
    print("📝 Для ручного запуска туннеля:")
    print("   lt -p 8080")
else:
    print("⚠️ ЕСТЬ ПРОБЛЕМЫ:")
    if not server_ok:
        print("  - Сервер не запущен")
    if not node_dir:
        print("  - Node.js не найден")
    print()
    print("Устрани проблемы и запусти тест снова")

print()
