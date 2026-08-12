#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_docker_setup.py
Тест конфигурации Docker и PWA
"""

import os
import sys
import json
from pathlib import Path

COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'END': '\033[0m'
}

def color(text, color_name):
    return f"{COLORS.get(color_name, '')}{text}{COLORS['END']}"

def check_file(filepath, description):
    """Проверка существования файла"""
    if os.path.exists(filepath):
        print(f"  ✅ {description}: {filepath}")
        return True
    else:
        print(f"  ❌ {description}: {filepath} не найден")
        return False

def check_env_variable(var_name, required=True):
    """Проверка переменной окружения"""
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    if value:
        if 'TOKEN' in var_name or 'PASSWORD' in var_name or 'SECRET' in var_name:
            masked = value[:3] + '***' + value[-3:] if len(value) > 6 else '***'
            print(f"  ✅ {var_name}: {masked}")
        else:
            print(f"  ✅ {var_name}: {value}")
        return True
    else:
        if required:
            print(f"  ❌ {var_name}: не установлена")
            return False
        else:
            print(f"  ⚠️  {var_name}: не установлена (опционально)")
            return True

def check_docker():
    """Проверка Docker"""
    print(color("\n🐳 Проверка Docker...", 'BLUE'))
    
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✅ Docker: {result.stdout.strip()}")
        else:
            print(f"  ❌ Docker: не найден")
            return False
    except Exception as e:
        print(f"  ❌ Docker: ошибка проверки - {e}")
        return False
    
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✅ Docker Compose: {result.stdout.strip()}")
        else:
            print(f"  ❌ Docker Compose: не найден")
            return False
    except Exception as e:
        print(f"  ❌ Docker Compose: ошибка проверки - {e}")
        return False
    
    return True

def check_docker_files():
    """Проверка Docker файлов"""
    print(color("\n📁 Проверка Docker файлов...", 'BLUE'))
    
    files = [
        ('Dockerfile', 'Dockerfile'),
        ('docker-compose.yml', 'Docker Compose'),
        ('.env', 'Environment file'),
        ('.env.example', 'Environment example'),
        ('.dockerignore', 'Docker ignore'),
        ('nginx/nginx.conf', 'Nginx config'),
        ('scripts/init_db.sql', 'DB init script'),
        ('scripts/migrate_sqlite_to_postgres.py', 'Migration script'),
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file(filepath, description):
            all_exist = False
    
    return all_exist

def check_env_config():
    """Проверка .env конфигурации"""
    print(color("\n⚙️  Проверка .env конфигурации...", 'BLUE'))
    
    required_vars = [
        'FLASK_ENV',
        'SECRET_KEY',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'TELEGRAM_BOT_TOKEN',
        'VK_GROUP_ID',
        'LOCAL_IP',
        'PUBLIC_IP',
    ]
    
    all_set = True
    for var in required_vars:
        if not check_env_variable(var, required=True):
            all_set = False
    
    return all_set

def check_pwa_files():
    """Проверка PWA файлов"""
    print(color("\n📱 Проверка PWA файлов...", 'BLUE'))
    
    files = [
        ('static/manifest.json', 'PWA Manifest'),
        ('static/js/sw.js', 'Service Worker'),
        ('static/js/pwa-installer.js', 'PWA Installer'),
        ('static/js/barcode-scanner.js', 'Barcode Scanner'),
        ('templates/offline.html', 'Offline Page'),
    ]
    
    all_exist = True
    for filepath, description in files:
        if not check_file(filepath, description):
            all_exist = False
    
    # Проверка manifest.json
    try:
        with open('static/manifest.json', 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            print(f"  ✅ Manifest name: {manifest.get('name', 'N/A')}")
            print(f"  ✅ Manifest icons: {len(manifest.get('icons', []))} icons")
            print(f"  ✅ Manifest shortcuts: {len(manifest.get('shortcuts', []))} shortcuts")
    except Exception as e:
        print(f"  ❌ Manifest: ошибка чтения - {e}")
        all_exist = False
    
    return all_exist

def check_web_config():
    """Проверка web_config.py"""
    print(color("\n🔧 Проверка web_config.py...", 'BLUE'))
    
    try:
        # Проверка что файл существует
        if not os.path.exists('web_config.py'):
            print(f"  ❌ web_config.py не найден")
            return False
        
        # Проверка что импортируется dotenv
        with open('web_config.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'from dotenv import load_dotenv' in content:
            print(f"  ✅ dotenv импорт найден")
        else:
            print(f"  ❌ dotenv импорт не найден")
            return False
        
        if 'USE_POSTGRES' in content:
            print(f"  ✅ PostgreSQL поддержка добавлена")
        else:
            print(f"  ⚠️  PostgreSQL поддержка не найдена")
        
        if 'DOCKER_MODE' in content:
            print(f"  ✅ Docker режим поддерживается")
        else:
            print(f"  ⚠️  Docker режим не поддерживается")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка проверки: {e}")
        return False

def check_requirements():
    """Проверка requirements.txt"""
    print(color("\n📦 Проверка requirements.txt...", 'BLUE'))
    
    required_packages = [
        'python-dotenv',
        'psycopg2-binary',
        'redis',
        'gunicorn',
        'gevent',
    ]
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        all_found = True
        for package in required_packages:
            if package.lower() in content:
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package} не найден")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ❌ Ошибка проверки: {e}")
        return False

def main():
    """Основная функция"""
    print(color("=" * 60, 'BLUE'))
    print(color("🐳 DOCKER + PWA SETUP TEST", 'GREEN'))
    print(color("=" * 60, 'BLUE'))
    print(f"📁 Проект: {os.path.abspath('.')}")
    print(f"📅 Дата: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    results = {
        'Docker': check_docker(),
        'Docker Files': check_docker_files(),
        'Environment': check_env_config(),
        'PWA Files': check_pwa_files(),
        'Web Config': check_web_config(),
        'Requirements': check_requirements(),
    }
    
    print(color("\n" + "=" * 60, 'BLUE'))
    print(color("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ", 'GREEN'))
    print(color("=" * 60, 'BLUE'))
    
    for test_name, passed in results.items():
        status = color("✅ PASSED", 'GREEN') if passed else color("❌ FAILED", 'RED')
        print(f"{test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(color("\n" + "=" * 60, 'BLUE'))
    
    if total_passed == total_tests:
        print(color("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!", 'GREEN'))
        print(color("\n🚀 Можете запускать Docker:", 'GREEN'))
        print("   docker-compose up -d --build")
    else:
        print(color(f"⚠️  Пройдено {total_passed}/{total_tests} проверок", 'YELLOW'))
        print(color("\n❌ Исправьте ошибки перед запуском Docker", 'RED'))
    
    print(color("=" * 60, 'BLUE'))
    
    return 0 if total_passed == total_tests else 1

if __name__ == '__main__':
    sys.exit(main())
