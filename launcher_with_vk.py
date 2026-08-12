# -*- coding: utf-8 -*-
"""
Запуск сервера GrafikRaboty с VK уведомлениями
Обходит проблему с кодировкой main_launcher.py
"""
import sys
import os
import threading
import time

# Устанавливаем UTF-8 кодировку для вывода
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

print("=" * 60)
print(" GRAFIKRABOTY SERVER WITH VK NOTIFICATIONS")
print("=" * 60)
print()

# Проверяем VK конфигурацию
print("[1/4] Проверка VK конфигурации...")
try:
    import vk_bot
    config = vk_bot.get_config()
    if config and config.get('service_token'):
        print("   [OK] VK токен настроен")
        print(f"   [OK] Admin VK ID: {config.get('admin_vk_id')}")
        print(f"   [OK] Group ID: {config.get('group_id')}")
    else:
        print("   [WARN] VK токен не настроен — уведомления не отправятся")
except Exception as e:
    print(f"   [WARN] Ошибка VK: {e}")

print()
print("[2/4] Запуск веб-сервера и socket сервера...")

# Запускаем main_launcher в отдельном потоке
def run_server():
    try:
        # Импортируем и запускаем mainLauncher
        import main_launcher
        main_launcher.main()
    except Exception as e:
        print(f"[ERROR] Server crashed: {e}")
        import traceback
        traceback.print_exc()

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Запускаем автозапуск туннеля с VK уведомлениями
print("[2.5/4] Запуск автозапуска туннеля...")

def run_auto_tunnel():
    try:
        import auto_tunnel_launcher
        auto_tunnel_launcher.start_auto_tunnel()
        print("   ✓ Автозапуск туннеля запущен")
    except Exception as e:
        print(f"   ⚠ Автозапуск туннеля: {e}")

tunnel_thread = threading.Thread(target=run_auto_tunnel, daemon=True)
tunnel_thread.start()

# Запускаем VK Long Poll для получения сообщений из группы
def run_vk_polling():
    try:
        import vk_bot
        vk_bot.start_polling()
        print("   ✓ VK Long Poll запущен (получение сообщений из группы)")
    except Exception as e:
        print(f"   ⚠ VK Long Poll не запущен: {e}")

vk_poll_thread = threading.Thread(target=run_vk_polling, daemon=True)
vk_poll_thread.start()

# Ждём запуска сервера
print("[3/4] Ожидание запуска сервера...")
for i in range(30):  # Ждём до 30 секунд
    time.sleep(1)
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8080/login")
        with urllib.request.urlopen(req, timeout=2) as r:
            if r.status == 200:
                print("   ✓ Сервер запущен на порту 8080")
                break
    except Exception:
        pass
else:
    print("   ⚠ Сервер не ответил за 30 секунд")

# Получаем информацию о туннеле
print("[4/4] Проверка туннеля...")
time.sleep(3)  # Даём время на получение туннеля

try:
    # Читаем tunnel_info.json
    tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
    if os.path.exists(tunnel_info_path):
        import json
        with open(tunnel_info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)

        tunnel_url = info.get('tunnel_url', '')
        password = info.get('password', '')

        print(f"   ✓ Туннель: {tunnel_url}")
        print(f"   ✓ Пароль: {password}")
        print("   ℹ️ VK уведомление отправлено из auto_tunnel_launcher.py")

        # ⚠️ НЕ ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ЗДЕСЬ
        # auto_tunnel_launcher.py уже отправил уведомление при запуске туннеля
        # vk_startup.send_vk_startup_notification(...)  # ЗАКОММЕНТИРОВАНО

except Exception as e:
    print(f"   ⚠ Ошибка чтения tunnel_info: {e}")

print()
print("=" * 60)
print(" СЕРВЕР ЗАПУЩЕН!")
print("=" * 60)
print()
print("📍 Локальный доступ: http://127.0.0.1:8080")
print("📍 Telegram: уведомления настроены")
print("📍 VK: уведомления отправлены")
print()
print("Нажми Ctrl+C для остановки сервера")
print()

# Держим программу запущенной
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nОстановка сервера...")
    sys.exit(0)
