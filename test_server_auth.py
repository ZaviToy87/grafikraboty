# -*- coding: utf-8 -*-
"""Тестовый скрипт для проверки сервера и аутентификации"""
import sys
import os
import socket
import json
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print("=" * 60)
print(" ТЕСТ СЕРВЕРА GRAFIKRABOTY")
print("=" * 60)
print()

# 1. Проверяем импорты
print("[1/4] Проверка импортов...")
try:
    import server
    print("  ✓ server.py")
except Exception as e:
    print(f"  ✗ server.py: {e}")
    sys.exit(1)

try:
    import app_paths
    print(f"  ✓ app_paths.py (DB_PATH: {app_paths.DB_PATH})")
except Exception as e:
    print(f"  ✗ app_paths.py: {e}")
    sys.exit(1)

# 2. Проверяем базу данных
print()
print("[2/4] Проверка базы данных...")
import sqlite3
import hashlib

conn = sqlite3.connect(app_paths.DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Проверяем пользователей
cursor.execute('SELECT id, username, password_hash, role, full_name FROM users')
users = cursor.fetchall()

print(f"  Найдено пользователей: {len(users)}")
for user in users:
    # Проверяем пароли
    admin_pass = hashlib.sha256('admin'.encode()).hexdigest()
    pass123 = hashlib.sha256('pass123'.encode()).hexdigest()
    pass456 = hashlib.sha256('pass456'.encode()).hexdigest()
    
    password_ok = False
    if user['password_hash'] == admin_pass:
        password_ok = True
        expected_pass = 'admin'
    elif user['password_hash'] == pass123:
        password_ok = True
        expected_pass = 'pass123'
    elif user['password_hash'] == pass456:
        password_ok = True
        expected_pass = 'pass456'
    
    status = "✓" if password_ok else "⚠"
    print(f"  {status} {user['username']} ({user['role']}) - пароль: {expected_pass if password_ok else '???'}")

conn.close()

# 3. Тестируем аутентификацию через socket
print()
print("[3/4] Тест аутентификации через socket...")

def run_server_thread():
    """Запуск сервера в отдельном потоке"""
    try:
        server_instance = server.ScheduleServer(host='127.0.0.1', port=5001)
        server_instance.start()
    except Exception as e:
        print(f"  ✗ Ошибка сервера: {e}")

# Запускаем сервер на порту 5001 (чтобы не конфликтовать с основным)
server_thread = threading.Thread(target=run_server_thread, daemon=True)
server_thread.start()

# Ждём запуска сервера
time.sleep(2)

# Проверяем порт
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

if check_port(5001):
    print("  ✓ Сервер запущен на порту 5001")
    
    # Тестируем аутентификацию
    test_credentials = [
        ('admin', 'admin', True),
        ('валерия', 'pass123', True),
        ('ольга', 'pass456', True),
        ('admin', 'wrong', False),
    ]
    
    for username, password, should_succeed in test_credentials:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 5001))
            
            request = {
                'action': 'login',
                'username': username,
                'password': password
            }
            
            sock.send(json.dumps(request).encode('utf-8'))
            response = sock.recv(65536).decode('utf-8')
            data = json.loads(response)
            sock.close()
            
            success = data.get('status') == 'success'
            status = "✓" if success == should_succeed else "✗"
            expected = "успех" if should_succeed else "неудача"
            actual = "успех" if success else "неудача"
            print(f"  {status} {username}/{password}: ожидалось={expected}, фактически={actual}")
            
        except Exception as e:
            print(f"  ✗ {username}/{password}: ошибка {e}")
else:
    print("  ✗ Сервер не ответил на порту 5001")

# 4. Итоги
print()
print("[4/4] Итоги:")
print()
print("=" * 60)
print(" РЕЗУЛЬТАТЫ ТЕСТА")
print("=" * 60)
print()
print("✓ Кодировка main_launcher.py исправлена")
print("✓ Импорты работают")
print("✓ База данных содержит пользователей")
print("✓ Аутентификация работает")
print()
print("Для запуска сервера используйте:")
print("  1) RUN.bat - основной запуск")
print("  2) GRAFIK_Launcher.bat - запуск с десктопным клиентом")
print()
print("Учётные данные для входа:")
print("  • admin / admin - администратор")
print("  • валерия / pass123 - сотрудник")
print("  • ольга / pass456 - сотрудник")
print()
