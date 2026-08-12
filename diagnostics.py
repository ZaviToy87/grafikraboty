# -*- coding: utf-8 -*-
"""
diagnostics.py - Полная диагностика системы GrafikRaboty
Запускать при остановленном сервере
"""
import sqlite3
import os
import json

DB_PATH = 'schedule.db'

def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}\n")

def check_db_structure():
    """Проверка структуры БД"""
    print_header("1. СТРУКТУРА БАЗЫ ДАННЫХ")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ БД не найдена: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"✓ Таблицы ({len(tables)}): {', '.join(tables)}")
    
    # Структура work_journal_entries
    print("\n📊 Таблица work_journal_entries:")
    cursor.execute('PRAGMA table_info(work_journal_entries)')
    cols = cursor.fetchall()
    for col in cols:
        print(f"  - {col[1]} ({col[2]})")
    
    # Проверяем есть ли entry_type
    col_names = [c[1] for c in cols]
    if 'entry_type' in col_names:
        print("  ⚠️  КОЛОНКА entry_type НАЙДЕНА (должно быть kind)")
    if 'kind' in col_names:
        print("  ✓ КОЛОНКА kind присутствует")
    if 'user_id' in col_names:
        print("  ✓ КОЛОНКА user_id присутствует")
    
    # Структура schedule
    print("\n📊 Таблица schedule:")
    cursor.execute('PRAGMA table_info(schedule)')
    cols = cursor.fetchall()
    for col in cols:
        print(f"  - {col[1]} ({col[2]})")
    
    # Данные
    print("\n📊 ДАННЫЕ В ТАБЛИЦАХ:")
    for table in ['users', 'tasks', 'schedule', 'work_journal_entries', 'files', 'chat_topics']:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} записей")
        except:
            print(f"  {table}: ошибка")
    
    # Последние записи schedule
    print("\n📊 ПОСЛЕДНИЕ 5 ЗАПИСЕЙ В schedule:")
    cursor.execute('SELECT id, user_id, year, month, day, task_ids FROM schedule ORDER BY id DESC LIMIT 5')
    for row in cursor.fetchall():
        print(f"  ID={row[0]}, user_id={row[1]}, date={row[2]}.{row[3]}.{row[4]}, task_ids={row[5]}")
    
    # Записи на март 2026
    print("\n📊 ЗАПИСИ НА МАРТ 2026 (22-23 число):")
    cursor.execute('SELECT id, user_id, day, task_ids FROM schedule WHERE year=2026 AND month=3 AND day IN (22,23) ORDER BY day, user_id')
    for row in cursor.fetchall():
        print(f"  ID={row[0]}, user_id={row[1]}, day={row[2]}, task_ids={row[3]}")
    
    conn.close()

def check_files():
    """Проверка файлов системы"""
    print_header("2. ФАЙЛЫ СИСТЕМЫ")
    
    required_files = [
        'server.py',
        'web_server.py',
        'web_api.py',
        'web_work_journal.py',
        'web_auth.py',
        'web_chat.py',
        'web_vk_chat.py',
        'web_config.py',
        'vk_bot.py',
        'vk_verification.py',
        'telegram_config.json',
        'vk_config.json',
    ]
    
    for f in required_files:
        if os.path.exists(f):
            print(f"  ✓ {f}")
        else:
            print(f"  ❌ {f} - НЕ НАЙДЕН")
    
    # Проверка логов
    print("\n📊 ЛОГИ:")
    logs_dir = 'logs'
    if os.path.exists(logs_dir):
        logs = os.listdir(logs_dir)
        print(f"  Папка logs/: {len(logs)} файлов")
        for log in logs[-5:]:  # Последние 5
            print(f"    - {log}")
    else:
        print("  ❌ Папка logs/ не найдена")

def check_config():
    """Проверка конфигурации"""
    print_header("3. КОНФИГУРАЦИЯ")
    
    # Telegram
    print("\n📊 Telegram:")
    if os.path.exists('telegram_config.json'):
        try:
            with open('telegram_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"  ✓ Token: {'настроен' if config.get('token') else '❌ пустой'}")
            print(f"  ✓ Chat IDs: {config.get('chat_ids', [])}")
        except Exception as e:
            print(f"  ❌ Ошибка чтения: {e}")
    else:
        print("  ❌ Файл не найден")
    
    # VK
    print("\n📊 VK:")
    if os.path.exists('vk_config.json'):
        try:
            with open('vk_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"  ✓ Service Token: {'настроен' if config.get('service_token') else '❌ пустой'}")
            print(f"  ✓ Admin VK ID: {config.get('admin_vk_id')}")
            print(f"  ✓ Group ID: {config.get('group_id')}")
            print(f"  ✓ Chat Peer ID: {config.get('chat_peer_id')}")
        except Exception as e:
            print(f"  ❌ Ошибка чтения: {e}")
    else:
        print("  ❌ Файл не найден")

def check_routes():
    """Проверка роутов"""
    print_header("4. API РОУТЫ (проверка структуры)")
    
    files_to_check = {
        'web_api.py': ['/api/schedule', '/api/tasks', '/api/files', '/api/users', '/api/reminders'],
        'web_auth.py': ['/api/vk/send-code', '/api/vk/verify-code'],
        'web_work_journal.py': ['/api/work-journal'],
        'web_chat.py': ['/api/chat'],
        'web_converter.py': ['/api/converter'],
    }
    
    for filename, expected_routes in files_to_check.items():
        print(f"\n📊 {filename}:")
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for route in expected_routes:
                # Ищем роуты с этим префиксом
                if f"@..._bp.route('{route}" in content or f'@..._bp.route("{route}' in content:
                    print(f"  ✓ {route}")
                elif f'@..._bp.route(\'{route}' in content:
                    print(f"  ✓ {route}")
                else:
                    # Проверяем есть ли вообще
                    if route.replace('/api', '') in content:
                        print(f"  ⚠️  {route} - найден без /api")
                    else:
                        print(f"  ❌ {route} - НЕ НАЙДЕН")
        else:
            print(f"  ❌ Файл не найден")

def check_static():
    """Проверка статики"""
    print_header("5. СТАТИКА И ШАБЛОНЫ")
    
    dirs_to_check = ['static', 'templates', 'static/uploads', 'static/css', 'static/js']
    
    for d in dirs_to_check:
        if os.path.exists(d):
            files = os.listdir(d)
            print(f"  ✓ {d}/ - {len(files)} файлов/папок")
        else:
            print(f"  ❌ {d}/ - НЕ НАЙДЕНА")

def main():
    print("\n" + "="*60)
    print(" GRAFIKRABOTY - ПОЛНАЯ ДИАГНОСТИКА СИСТЕМЫ")
    print("="*60)
    print(f"Рабочая папка: {os.path.abspath('.')}")
    print(f"Дата проверки: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    check_db_structure()
    check_files()
    check_config()
    check_routes()
    check_static()
    
    print_header("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("Скопируйте этот отчёт и отправьте разработчику")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
