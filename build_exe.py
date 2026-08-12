# -*- coding: utf-8 -*-
"""
build_exe.py — Сборка EXE файла GrafikRaboty

Создаёт standalone executable для запуска без Python
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================

PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "exe_build"
DIST_DIR = PROJECT_ROOT / "exe_dist"
EXE_NAME = "GrafikRaboty_Server"

# ==========================================
# ФУНКЦИИ
# ==========================================

def log(message):
    """Вывод лога"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_pyinstaller():
    """Запустить PyInstaller"""
    log("🔨 Запуск PyInstaller...")
    
    # Команда
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", EXE_NAME,
        "--onedir",  # Папка с exe (надёжнее)
        "--console",  # Показывать консоль
        "--noconfirm",
        "--clean",
        "--hidden-import=flask",
        "--hidden-import=flask_socketio",
        "--hidden-import=socketio",
        "--hidden-import=jinja2",
        "--hidden-import=werkzeug",
        "--hidden-import=sqlalchemy",
        "--hidden-import=telegram",
        "--hidden-import=vk_api",
        "--hidden-import=psutil",
        "--hidden-import=aiohttp",
        "--hidden-import=selenium",
        "--hidden-import=pyautogui",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=PIL",
        "--hidden-import=socketio",
        "--hidden-import=engineio",
        "--hidden-import=flask_socketio",
        "--hidden-import=simple_websocket",
        "--hidden-import=websocket",
        "--add-data", f"templates{os.pathsep}templates",
        "--add-data", f"static{os.pathsep}static",
        "--add-data", f".mcp{os.pathsep}.mcp",
        "--add-data", "telegram_config.json;.",
        "--add-data", "vk_config.json;.",
        "--add-data", "schedule.db;.",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--workpath", str(BUILD_DIR),
        "--distpath", str(DIST_DIR),
        "web_server.py",
    ]
    
    log(f"Команда: {' '.join(cmd)}")
    
    # Запуск
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log("✅ PyInstaller завершён")
        if result.stdout:
            log(f"Вывод:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Ошибка PyInstaller: {e}")
        if e.stderr:
            log(f"Ошибка:\n{e.stderr}")
        return False


def copy_additional_files():
    """Копировать дополнительные файлы в дистрибутив"""
    log("📁 Копирование дополнительных файлов...")
    
    dist_exe_dir = DIST_DIR / EXE_NAME
    
    # Файлы для запуска
    additional_files = [
        "INSTALL.bat",
        "Start_GrafikRaboty.bat",
        "README.md",
        "requirements.txt",
    ]
    
    for file in additional_files:
        src = PROJECT_ROOT / "installer_build" / file
        if src.exists():
            shutil.copy2(src, dist_exe_dir / file)
            log(f"  📄 {file}")
    
    # MCP система
    mcp_src = PROJECT_ROOT / ".mcp"
    mcp_dst = dist_exe_dir / ".mcp"
    if mcp_src.exists() and not mcp_dst.exists():
        shutil.copytree(mcp_src, mcp_dst)
        log("  📁 .mcp/")
    
    # Логи
    logs_dir = dist_exe_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log("  📁 logs/")


def create_launcher():
    """Создать удобный лаунчер"""
    launcher_content = '''@echo off
chcp 65001 >nul
title GrafikRaboty Server
echo ========================================
echo  GrafikRaboty Server v4.9
echo ========================================
echo.
echo Запуск сервера...
echo.

GrafikRaboty_Server.exe

echo.
echo ========================================
echo  Сервер остановлен
echo ========================================
pause
'''
    
    dist_exe_dir = DIST_DIR / EXE_NAME
    launcher_path = dist_exe_dir / "RUN.bat"
    
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    log("📄 Создан RUN.bat")


def create_readme_exe():
    """Создать README для EXE версии"""
    readme_content = f'''# 🚀 GrafikRaboty Server v4.9 — EXE Версия

**Дата сборки:** {datetime.now().strftime("%Y-%m-%d")}

---

## ⚡ БЫСТРЫЙ ЗАПУСК

### Вариант 1: Через лаунчер
```bash
RUN.bat
```

### Вариант 2: Напрямую
```bash
GrafikRaboty_Server.exe
```

### Вариант 3: С параметрами
```bash
GrafikRaboty_Server.exe --port 8080 --debug
```

---

## 📋 КОМПОНЕНТЫ

### Веб-сервер
- **Порт:** 8080
- **URL:** http://localhost:8080
- **Лог:** logs/web_server.log

### MCP Система
- **Порт:** 8081
- **Запуск:** Start_MCP_Server.bat
- **Лог:** logs/mcp.log

---

## 🔧 НАСТРОЙКА

### 1. Telegram
Заполните `telegram_config.json`:
```json
{{
  "token": "YOUR_BOT_TOKEN",
  "chat_ids": [123456789],
  "admin_user_id": 701768868
}}
```

### 2. VK
Заполните `vk_config.json`:
```json
{{
  "token": "VK_SERVICE_TOKEN",
  "group_id": 123456789,
  "chat_peer_id": 2000000001
}}
```

---

## 📊 УЧЁТНЫЕ ДАННЫЕ

### Администратор
- **Логин:** admin
- **Пароль:** admin

### Сотрудники
- **Логин:** валерия / ольга
- **Пароль:** pass123 / pass456

---

## 🛠️ МОДИ

### MCP Агенты
Запуск через `Start_MCP_Server.bat`

Агенты:
1. code_fixer
2. server_controller
3. api_tester
4. ui_verifier
5. security_auditor
6. desktop_automation
7. code_analyzer
8. vk_sync_monitor
9. integration_tester

---

## 📝 ЛОГИРОВАНИЕ

Логи в папке `logs/`:
- `web_server.log` — веб-сервер
- `mcp.log` — MCP система
- `tunnel.log` — туннель

---

## ❓ УСТРАНЕНИЕ НЕИСПРАВНОСТЕЙ

### Порт 8080 занят
```bash
netstat -ano | findstr :8080
taskkill /F /PID <PID>
```

### Ошибка запуска
1. Проверьте, что файлы на месте
2. Проверьте логи в `logs/`
3. Убедитесь, что порты свободны

---

**Версия:** v4.9  
**Дата:** {datetime.now().strftime("%Y-%m-%d")}  
**Сборка:** EXE Standalone
'''
    
    readme_path = DIST_DIR / EXE_NAME / "README_EXE.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    log("📄 Создан README_EXE.md")


def main():
    log("=" * 60)
    log("🔨 СБОРКА EXE GRAFIKRABOTY v4.9")
    log("=" * 60)
    log("")
    
    # Проверка PyInstaller
    log("📋 Проверка зависимостей...")
    try:
        import PyInstaller
        log(f"✅ PyInstaller установлен: {PyInstaller.__version__}")
    except ImportError:
        log("❌ PyInstaller не найден!")
        log("Установите: pip install pyinstaller")
        return False
    
    # Очистка
    log("")
    log("🧹 Очистка старых сборок...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    log("✅ Готово")
    
    # PyInstaller
    log("")
    if not run_pyinstaller():
        log("❌ Сборка не удалась!")
        return False
    
    # Дополнительные файлы
    log("")
    copy_additional_files()
    
    # Лаунчер
    log("")
    create_launcher()
    
    # README
    create_readme_exe()
    
    # Итог
    log("")
    log("=" * 60)
    log("✅ EXE СБОРКА ЗАВЕРШЕНА")
    log("=" * 60)
    log("")
    log(f"📂 Директория: {DIST_DIR / EXE_NAME}")
    log("")
    log("Для запуска:")
    log("  1. Перейдите в папку")
    log("  2. Заполните конфиги")
    log("  3. Запустите RUN.bat или GrafikRaboty_Server.exe")
    log("")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
