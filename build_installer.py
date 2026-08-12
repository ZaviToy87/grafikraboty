# -*- coding: utf-8 -*-
"""
build_installer.py — Сборщик полного установочного пакета GrafikRaboty

Создаёт дистрибутив со всеми компонентами:
- Веб-сервер с Flask
- Базы данных
- MCP система с агентами
- Все зависимости
- Установочный скрипт
"""
import os
import sys
import shutil
import zipfile
import json
import subprocess
from datetime import datetime
from pathlib import Path

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================

PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "installer_build"
DIST_DIR = PROJECT_ROOT / "installer_dist"
INSTALLER_NAME = "GrafikRaboty_Installer_v4.9"

# Что включаем
INCLUDE_DIRS = [
    "static",
    "templates",
    ".mcp",
    "sales",
    "uploads",
    "logs",
]

INCLUDE_FILES = [
    "web_server.py",
    "web_config.py",
    "web_auth.py",
    "web_api.py",
    "web_chat.py",
    "web_work_journal.py",
    "web_barcodes.py",
    "web_converter.py",
    "web_admin.py",
    "web_vk_chat.py",
    "vk_bot.py",
    "server.py",
    "recurring_schedule.py",
    "requirements.txt",
    "schedule.db",
    "telegram_config.json",
    "vk_config.json",
    "telegram_seen_users.json",
]

# Исключения
EXCLUDE_PATTERNS = [
    "*.pyc",
    "__pycache__",
    ".venv",
    ".venv1",
    ".idea",
    ".cursor",
    ".gigaide",
    ".continue",
    "installer_build",
    "installer_dist",
    "build",
    "dist",
    "*.log",
    "*.pid",
    "backup_*",
]

# Зависимости для установки
PYTHON_VERSION = "3.11.9"
REQUIRED_PACKAGES = [
    "flask==2.0.1",
    "flask-socketio==5.3.0",
    "python-socketio==5.8.0",
    "sqlalchemy==1.4.23",
    "psutil==5.9.8",
    "python-telegram-bot==13.7",
    "vk-api==11.9.1",
    "aiohttp==3.9.1",
    "requests==2.31.0",
    "jinja2==3.0.3",
    "werkzeug==2.0.3",
    "pyautogui==0.9.54",
    "opencv-python==4.9.0.80",
    "numpy==1.26.3",
    "selenium==4.16.0",
    "pillow==10.2.0",
    "pyinstaller==6.3.0",
]


# ==========================================
# ФУНКЦИИ
# ==========================================

def log(message):
    """Вывод лога"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def clean_dir(directory):
    """Очистить директорию"""
    if directory.exists():
        log(f"Очистка {directory}...")
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def copy_file(src, dst):
    """Копировать файл с созданием директорий"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log(f"  📄 {src.name}")


def copy_tree(src, dst, exclude_patterns=None):
    """Копировать дерево с исключениями"""
    if exclude_patterns is None:
        exclude_patterns = []
    
    log(f"📁 Копирование {src.name}...")
    
    for item in src.rglob("*"):
        # Проверка исключений
        exclude = False
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                if item.match(pattern[1:]):
                    exclude = True
                    break
            elif item.name == pattern or item.parent.name == pattern:
                exclude = True
                break
        
        if exclude:
            continue
        
        if item.is_file():
            rel_path = item.relative_to(src)
            dst_path = dst / rel_path
            copy_file(item, dst_path)


def create_installer_script():
    """Создать скрипт установщика"""
    script_content = '''@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo  УСТАНОВКА GrafikRaboty v4.9
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo.
    echo Установите Python 3.11 с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python найден
python --version
echo.

REM Создание виртуального окружения
echo [1/4] Создание виртуального окружения...
if exist venv (
    echo   Удаление старого venv...
    rmdir /s /q venv
)
python -m venv venv
echo   ✅ Готово
echo.

REM Активация venv
echo [2/4] Активация виртуального окружения...
call venv\\Scripts\\activate.bat
echo   ✅ Готово
echo.

REM Установка зависимостей
echo [3/4] Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей!
    pause
    exit /b 1
)
echo   ✅ Готово
echo.

REM Инициализация БД
echo [4/4] Инициализация базы данных...
if not exist schedule.db (
    echo   Создание базы данных...
    python server.py --init-db
    if errorlevel 1 (
        echo ❌ Ошибка инициализации БД!
        pause
        exit /b 1
    )
) else (
    echo   ✅ База данных уже существует
)
echo.

REM Копирование конфигов
echo Копирование конфигурационных файлов...
if exist telegram_config.json.example (
    if not exist telegram_config.json (
        copy telegram_config.json.example telegram_config.json
        echo   ⚠️ telegram_config.json создан - заполните данными!
    )
)
if exist vk_config.json.example (
    if not exist vk_config.json (
        copy vk_config.json.example vk_config.json
        echo   ⚠️ vk_config.json создан - заполните данными!
    )
)
echo.

echo ========================================
echo  ✅ УСТАНОВКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Для запуска сервера выполните:
echo   call venv\\Scripts\\activate.bat
echo   python web_server.py
echo.
echo Или используйте:
echo   Start_GrafikRaboty.bat
echo.
pause
'''
    
    installer_path = BUILD_DIR / "INSTALL.bat"
    with open(installer_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    log(f"📄 Создан INSTALL.bat")


def create_start_script():
    """Создать скрипт запуска"""
    script_content = '''@echo off
chcp 65001 >nul
echo Запуск GrafikRaboty...
call venv\\Scripts\\activate.bat
python web_server.py
pause
'''
    
    start_path = BUILD_DIR / "Start_GrafikRaboty.bat"
    with open(start_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    log(f"📄 Создан Start_GrafikRaboty.bat")


def create_readme():
    """Создать README"""
    readme_content = f'''# 📦 GrafikRaboty v4.9 — Установочный пакет

**Дата сборки:** {datetime.now().strftime("%Y-%m-%d")}

---

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Установка
```bash
INSTALL.bat
```

### 2. Настройка
Заполните конфигурационные файлы:
- `telegram_config.json` — токен Telegram бота
- `vk_config.json` — токен VK группы

### 3. Запуск
```bash
Start_GrafikRaboty.bat
```

Или вручную:
```bash
call venv\\Scripts\\activate.bat
python web_server.py
```

### 4. Открыть в браузере
http://localhost:8080

---

## 📋 КОМПОНЕНТЫ

### Веб-сервер
- **Порт:** 8080
- **Фреймворк:** Flask + Socket.IO
- **БД:** SQLite (schedule.db)

### MCP Система
- **Порт:** 8081
- **Агенты:** 9 штук
- **Запуск:** Start_MCP_Server.bat

### Telegram Бот
- **Интеграция:** полная
- **Команды:** /start, /help, /search, /read, /task

### VK Интеграция
- **Чат:** синхронизация с веб-чатом
- **Сообщения:** двусторонняя отправка

---

## 🔧 МОДУЛИ

1. **Календарь** — график работ
2. **Задачи** — управление задачами
3. **Файлы** — файловое хранилище
4. **Чат** — корпоративный мессенджер
5. **Рабочий журнал** — учёт смен
6. **Конвертер ценников** — печать ценников
7. **Штрих-коды** — генерация и печать
8. **Админ-панель** — управление системой

---

## 📊 БАЗЫ ДАННЫХ

### schedule.db (12 таблиц)
- users — пользователи
- tasks — задачи
- work_schedule — график работ
- work_sessions — фактические смены
- work_journal_entries — записи журнала
- chat_messages — сообщения чата
- chat_topics — темы чата
- files — файлы
- audit_log — аудит
- barcodes — штрих-коды
- colleague_tasks — задачи коллег
- salary_adjustments — корректировки зарплаты

---

## 🔐 УЧЁТНЫЕ ДАННЫЕ ПО УМОЛЧАНИЮ

### Администратор
- **Логин:** admin
- **Пароль:** admin

### Сотрудники
- **Логин:** валерия / ольга
- **Пароль:** pass123 / pass456

---

## ⚙️ НАСТРОЙКА

### Telegram
1. Создайте бота через @BotFather
2. Получите токен
3. Заполните `telegram_config.json`:
```json
{{
  "token": "YOUR_BOT_TOKEN",
  "chat_ids": [123456789],
  "admin_user_id": 701768868
}}
```

### VK
1. Создайте сообщество
2. Получите сервисный токен
3. Заполните `vk_config.json`:
```json
{{
  "token": "VK_SERVICE_TOKEN",
  "group_id": 123456789,
  "chat_peer_id": 2000000001
}}
```

---

## 🛠️ МОДИ

### MCP Агенты (9 штук)
1. **code_fixer** — исправление кода
2. **server_controller** — мониторинг сервера
3. **api_tester** — тестирование API
4. **ui_verifier** — проверка UI
5. **security_auditor** — аудит безопасности
6. **desktop_automation** — автоматизация
7. **code_analyzer** — анализ кода
8. **vk_sync_monitor** — синхронизация VK
9. **integration_tester** — интеграционное тестирование

Запуск MCP:
```bash
Start_MCP_Server.bat
```

API MCP: http://localhost:8081

---

## 📝 ЛОГИРОВАНИЕ

Логи сохраняются в:
- `logs/web_server.log` — веб-сервер
- `logs/mcp.log` — MCP система
- `logs/tunnel.log` — туннель

---

## 🔧 УСТРАНЕНИЕ НЕИСПРАВНОСТЕЙ

### Порт 8080 занят
```bash
Освободить_порт_8080.bat
```

### Ошибка БД
```bash
python check_db.py
python fix_db_integrity.py
```

### Проблемы с запуском
1. Проверьте Python: `python --version`
2. Проверьте зависимости: `pip list`
3. Переустановите зависимости: `pip install -r requirements.txt --force-reinstall`

---

## 📞 ПОДДЕРЖКА

При проблемах:
1. Проверьте логи в `logs/`
2. Проверьте конфиги (`telegram_config.json`, `vk_config.json`)
3. Убедитесь, что порты 8080 и 8081 свободны

---

**Версия:** v4.9  
**Дата:** {datetime.now().strftime("%Y-%m-%d")}  
**Сборка:** Полный установочный пакет
'''
    
    readme_path = BUILD_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    log(f"📄 Создан README.md")


def create_requirements():
    """Создать requirements.txt"""
    req_path = BUILD_DIR / "requirements.txt"
    with open(req_path, 'w', encoding='utf-8') as f:
        for package in REQUIRED_PACKAGES:
            f.write(f"{package}\n")
    log(f"📄 Создан requirements.txt")


def create_archive():
    """Создать ZIP архив"""
    clean_dir(DIST_DIR)
    
    archive_name = DIST_DIR / f"{INSTALLER_NAME}.zip"
    log(f"📦 Создание архива {archive_name.name}...")
    
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(BUILD_DIR.parent)
                zipf.write(file_path, arcname)
                log(f"  + {arcname}")
    
    log(f"✅ Архив создан: {archive_name.name}")
    log(f"📊 Размер: {archive_name.stat().st_size / 1024 / 1024:.2f} MB")


# ==========================================
# ОСНОВНАЯ ФУНКЦИЯ
# ==========================================

def main():
    log("=" * 60)
    log("🔨 СБОРКА УСТАНОВОЧНОГО ПАКЕТА GRAFIKRABOTY v4.9")
    log("=" * 60)
    log("")
    
    # Очистка
    clean_dir(BUILD_DIR)
    log("")
    
    # Копирование директорий
    log("📁 Копирование директорий...")
    for dir_name in INCLUDE_DIRS:
        src = PROJECT_ROOT / dir_name
        if src.exists():
            copy_tree(src, BUILD_DIR / dir_name, EXCLUDE_PATTERNS)
    log("")
    
    # Копирование файлов
    log("📄 Копирование файлов...")
    for file_name in INCLUDE_FILES:
        src = PROJECT_ROOT / file_name
        if src.exists():
            copy_file(src, BUILD_DIR / file_name)
    log("")
    
    # Копирование MCP
    log("🤖 Копирование MCP системы...")
    mcp_src = PROJECT_ROOT / ".mcp"
    if mcp_src.exists():
        copy_tree(mcp_src, BUILD_DIR / ".mcp", ["__pycache__", "*.log"])
    log("")
    
    # Создание скриптов
    log("📝 Создание установочных скриптов...")
    create_installer_script()
    create_start_script()
    create_readme()
    create_requirements()
    log("")
    
    # Создание архива
    log("📦 Создание ZIP архива...")
    create_archive()
    log("")
    
    # Итог
    log("=" * 60)
    log("✅ СБОРКА ЗАВЕРШЕНА")
    log("=" * 60)
    log("")
    log(f"📂 Директория сборки: {BUILD_DIR}")
    log(f"📦 Установочный архив: {DIST_DIR / INSTALLER_NAME}.zip")
    log("")
    log("Для установки:")
    log("  1. Распакуйте архив на целевом компьютере")
    log("  2. Запустите INSTALL.bat")
    log("  3. Заполните telegram_config.json и vk_config.json")
    log("  4. Запустите Start_GrafikRaboty.bat")
    log("")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"❌ Ошибка сборки: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
