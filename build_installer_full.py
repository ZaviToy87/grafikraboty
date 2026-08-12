# -*- coding: utf-8 -*-
"""
build_installer_full.py — Полная сборка установщика GrafikRaboty

Этапы:
1. Сборка EXE через PyInstaller
2. Копирование всех необходимых файлов
3. Компиляция Inno Setup установщика
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
INSTALLER_BUILD_DIR = PROJECT_ROOT / "installer_build"
INSTALLER_OUTPUT_DIR = PROJECT_ROOT / "installer_dist"
EXE_NAME = "GrafikRaboty_Server"
ISS_FILE = PROJECT_ROOT / "grafikraboty_full_installer.iss"

INNO_SETUP_PATHS = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe",
]

# ==========================================
# ФУНКЦИИ
# ==========================================

def log(message):
    """Вывод лога"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_pyinstaller():
    """Шаг 1: Сборка EXE через PyInstaller"""
    log("=" * 70)
    log("🔨 ЭТАП 1: СБОРКА EXE ЧЕРЕЗ PYINSTALLER")
    log("=" * 70)
    log("")
    
    # Очистка старых сборок
    log("🧹 Очистка старых сборок...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        log("  Удалена папка build/")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        log("  Удалена папка dist/")
    log("")
    
    # Команда PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", EXE_NAME,
        "--onedir",
        "--console",
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
    
    log("🚀 Запуск PyInstaller...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log("✅ PyInstaller завершён успешно")
        
        # Проверяем что EXE создан
        exe_path = DIST_DIR / EXE_NAME / f"{EXE_NAME}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / 1024 / 1024
            log(f"✅ EXE файл создан: {exe_path.name} ({size_mb:.2f} MB)")
            return True
        else:
            log("❌ EXE файл не найден после сборки!")
            return False
            
    except subprocess.CalledProcessError as e:
        log(f"❌ Ошибка PyInstaller: {e}")
        if e.stderr:
            log(f"Ошибка:\n{e.stderr}")
        return False


def copy_additional_files_to_exe():
    """Шаг 2: Копирование дополнительных файлов в EXE дистрибутив"""
    log("")
    log("=" * 70)
    log("📁 ЭТАП 2: КОПИРОВАНИЕ ДОПОЛНИТЕЛЬНЫХ ФАЙЛОВ")
    log("=" * 70)
    log("")
    
    dist_exe_dir = DIST_DIR / EXE_NAME
    
    # Файлы для запуска
    additional_files = [
        ("installer_build/INSTALL.bat", "INSTALL.bat"),
        ("installer_build/Start_GrafikRaboty.bat", "Start_GrafikRaboty.bat"),
        ("installer_build/README.md", "README.md"),
        ("requirements.txt", "requirements.txt"),
    ]
    
    for src_rel, dst_name in additional_files:
        src = PROJECT_ROOT / src_rel
        dst = dist_exe_dir / dst_name
        if src.exists():
            shutil.copy2(src, dst)
            log(f"  📄 {dst_name}")
        else:
            log(f"  ⚠️  {src_rel} не найден")
    
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
    
    log("✅ Дополнительные файлы скопированы")
    return True


def create_launcher():
    """Шаг 3: Создание удобного лаунчера"""
    log("")
    log("=" * 70)
    log("📝 ЭТАП 3: СОЗДАНИЕ LAUNCHER")
    log("=" * 70)
    log("")
    
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
    return True


def create_readme_exe():
    """Шаг 4: Создание README для EXE версии"""
    log("")
    log("=" * 70)
    log("📄 ЭТАП 4: СОЗДАНИЕ README")
    log("=" * 70)
    log("")
    
    readme_content = f'''# 🚀 GrafikRaboty Server v4.9 — Полная Версия

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

---

## 📋 КОМПОНЕНТЫ

### Веб-сервер
- **Порт:** 8080
- **URL:** http://localhost:8080
- **Лог:** logs/web_server.log

### Socket-сервер
- **Порт:** 5000
- Для десктопного клиента

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
**Сборка:** Full Installer
'''
    
    readme_path = DIST_DIR / EXE_NAME / "README_EXE.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    log("📄 Создан README_EXE.md")
    return True


def prepare_installer_build():
    """Шаг 5: Подготовка папки installer_build"""
    log("")
    log("=" * 70)
    log("📦 ЭТАП 5: ПОДГОТОВКА INSTALLER_BUILD")
    log("=" * 70)
    log("")
    
    # Очищаем installer_build
    if INSTALLER_BUILD_DIR.exists():
        shutil.rmtree(INSTALLER_BUILD_DIR)
    
    INSTALLER_BUILD_DIR.mkdir()
    
    # Копируем всё из exe_dist/GrafikRaboty_Server
    dist_exe_dir = DIST_DIR / EXE_NAME
    if dist_exe_dir.exists():
        for item in dist_exe_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, INSTALLER_BUILD_DIR / item.name)
            else:
                shutil.copy2(item, INSTALLER_BUILD_DIR / item.name)
        log("✅ Файлы из exe_dist скопированы")
    
    # Копируем дополнительные файлы из корня
    root_files = [
        "schedule.db",
        "telegram_config.json",
        "vk_config.json",
        "telegram_seen_users.json",
        "Start_MCP_Server.bat",
    ]
    
    for file in root_files:
        src = PROJECT_ROOT / file
        if src.exists():
            shutil.copy2(src, INSTALLER_BUILD_DIR / file)
            log(f"  📄 {file}")
    
    # Копируем шаблоны и статику из оригинальных папок
    for dir_name in ["templates", "static", "uploads"]:
        src = PROJECT_ROOT / dir_name
        if src.exists():
            shutil.copytree(src, INSTALLER_BUILD_DIR / dir_name, dirs_exist_ok=True)
            log(f"  📁 {dir_name}/")
    
    # Копируем логи
    logs_src = PROJECT_ROOT / "logs"
    logs_dst = INSTALLER_BUILD_DIR / "logs"
    if logs_src.exists():
        shutil.copytree(logs_src, logs_dst, dirs_exist_ok=True)
        log("  📁 logs/")
    else:
        logs_dst.mkdir(exist_ok=True)
        log("  📁 logs/ (создана)")
    
    log("✅ Installer build готов")
    return True


def find_inno_setup():
    """Найти компилятор Inno Setup"""
    for path in INNO_SETUP_PATHS:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            return expanded
    return None


def compile_installer():
    """Шаг 6: Компиляция Inno Setup установщика"""
    log("")
    log("=" * 70)
    log("🔨 ЭТАП 6: КОМПИЛЯЦИЯ INNO SETUP")
    log("=" * 70)
    log("")
    
    inno_path = find_inno_setup()
    
    if not inno_path:
        log("❌ Inno Setup не найден!")
        log("")
        log("📥 Установите Inno Setup:")
        log("   https://jrsoftware.org/isdl.php#stable")
        log("")
        return False
    
    log(f"✅ Inno Setup найден: {inno_path}")
    
    # Создаём output директорию
    INSTALLER_OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Компиляция
    log("")
    log("🔨 Компиляция установщика...")
    
    cmd = [
        inno_path,
        str(ISS_FILE),
        f"/O{INSTALLER_OUTPUT_DIR}",
        "/Qp",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        log("✅ Компиляция завершена")
        if result.stdout:
            log(f"Вывод:\n{result.stdout}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        log(f"❌ Ошибка компиляции: {e}")
        if e.stderr:
            log(f"Ошибка:\n{e.stderr}")
        return False


def verify_and_archive():
    """Шаг 7: Проверка и создание ZIP архива"""
    log("")
    log("=" * 70)
    log("📦 ЭТАП 7: ПРОВЕРКА И АРХИВАЦИЯ")
    log("=" * 70)
    log("")
    
    if not INSTALLER_OUTPUT_DIR.exists():
        log("❌ Папка output не создана")
        return False
    
    # Поиск EXE файла установщика
    exe_files = list(INSTALLER_OUTPUT_DIR.glob("*.exe"))
    
    if not exe_files:
        log("❌ EXE файл установщика не найден")
        return False
    
    for exe_file in exe_files:
        size_mb = exe_file.stat().st_size / 1024 / 1024
        log(f"✅ Создан установщик: {exe_file.name}")
        log(f"📊 Размер: {size_mb:.2f} MB")
    
    # Создаём ZIP с EXE версией (альтернатива установщику)
    zip_name = f"GrafikRaboty_Server_EXE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = INSTALLER_OUTPUT_DIR / zip_name
    
    log("")
    log(f"📦 Создание ZIP архива: {zip_name}")
    
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in INSTALLER_BUILD_DIR.rglob('*'):
            if item.is_file():
                arcname = item.relative_to(INSTALLER_BUILD_DIR)
                zipf.write(item, arcname)
    
    zip_size_mb = zip_path.stat().st_size / 1024 / 1024
    log(f"✅ ZIP архив создан: {zip_name} ({zip_size_mb:.2f} MB)")
    
    return True


def main():
    log("")
    log("╔" + "=" * 68 + "╗")
    log("║  🚀 GRAFIKRABOTY v4.9 — ПОЛНАЯ СБОРКА УСТАНОВЩИКА          ║")
    log("╚" + "=" * 68 + "╝")
    log("")
    
    # Проверка Python зависимостей
    log("📋 Проверка зависимостей...")
    try:
        import PyInstaller
        log(f"✅ PyInstaller установлен: {PyInstaller.__version__}")
    except ImportError:
        log("❌ PyInstaller не найден!")
        log("Установите: pip install pyinstaller")
        return False
    
    try:
        log("✅ Все зависимости установлены")
        log("")
        
        # Этапы сборки
        if not run_pyinstaller():
            return False
        
        if not copy_additional_files_to_exe():
            return False
        
        if not create_launcher():
            return False
        
        if not create_readme_exe():
            return False
        
        if not prepare_installer_build():
            return False
        
        if not compile_installer():
            log("⚠️  Inno Setup не найден, пропускаем компиляцию")
            log("💡 Будет создана только EXE версия без установщика")
        else:
            if not verify_and_archive():
                return False
        
        # Итог
        log("")
        log("=" * 70)
        log("✅ СБОРКА ЗАВЕРШЕНА")
        log("=" * 70)
        log("")
        log(f"📂 Директория сборки: {INSTALLER_OUTPUT_DIR}")
        log("")
        log("Что создано:")
        log("  1. EXE версия (портативная) — для быстрого запуска")
        log("  2. ZIP архив — для распространения")
        log("  3. Inno Setup установщик — для полноценной установки")
        log("")
        log("Для установки:")
        log("  • Вариант 1: Запустить GrafikRaboty_Setup_v4.9.exe")
        log("  • Вариант 2: Распаковать ZIP и запустить RUN.bat")
        log("")
        
        return True
        
    except Exception as e:
        log(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
