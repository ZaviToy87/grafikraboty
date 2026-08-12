# -*- coding: utf-8 -*-
"""
build_inno_installer.py — Компиляция установщика Inno Setup

Создаёт полноценный EXE установщик из проекта
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================

PROJECT_ROOT = Path(__file__).parent
ISS_FILE = PROJECT_ROOT / "grafikraboty_full_installer.iss"
OUTPUT_DIR = PROJECT_ROOT / "installer_output"
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


def find_inno_setup():
    """Найти компилятор Inno Setup"""
    for path in INNO_SETUP_PATHS:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            return expanded
    return None


def check_source_files():
    """Проверить наличие исходных файлов"""
    log("📋 Проверка исходных файлов...")
    
    required_files = [
        "exe_dist/GrafikRaboty_Server/GrafikRaboty_Server.exe",
        "exe_dist/GrafikRaboty_Server/RUN.bat",
        "exe_dist/GrafikRaboty_Server/schedule.db",
        "exe_dist/GrafikRaboty_Server/templates",
        "exe_dist/GrafikRaboty_Server/static",
        "exe_dist/GrafikRaboty_Server/_internal",
    ]
    
    missing = []
    for file in required_files:
        file_path = PROJECT_ROOT / file
        if not file_path.exists():
            missing.append(file)
    
    if missing:
        log("❌ Отсутствуют файлы:")
        for file in missing:
            log(f"   - {file}")
        log("")
        log("💡 Запустите сначала: python build_exe.py")
        return False
    
    log("✅ Все файлы на месте")
    return True


def compile_installer():
    """Скомпилировать установщик"""
    inno_path = find_inno_setup()
    
    if not inno_path:
        log("❌ Inno Setup не найден!")
        log("")
        log("📥 Установите Inno Setup:")
        log("   https://jrsoftware.org/isdl.php#stable")
        log("")
        log("Или используйте:")
        log("   pip install pyinstaller (для EXE версии)")
        return False
    
    log(f"✅ Inno Setup найден: {inno_path}")
    
    # Компиляция
    log("")
    log("🔨 Компиляция установщика...")
    
    cmd = [
        inno_path,
        str(ISS_FILE),
        f"/O{OUTPUT_DIR}",
        "/Qp",  # Тихий режим с прогрессом
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
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
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False


def verify_output():
    """Проверить результат"""
    log("")
    log("📦 Проверка результата...")
    
    if not OUTPUT_DIR.exists():
        log("❌ Папка output не создана")
        return False
    
    # Поиск EXE файла
    exe_files = list(OUTPUT_DIR.glob("*.exe"))
    
    if not exe_files:
        log("❌ EXE файл не найден")
        return False
    
    for exe_file in exe_files:
        size_mb = exe_file.stat().st_size / 1024 / 1024
        log(f"✅ Создан установщик: {exe_file.name}")
        log(f"📊 Размер: {size_mb:.2f} MB")
    
    return True


def main():
    log("=" * 70)
    log("🔨 СБОРКА УСТАНОВЩИКА INNO SETUP GRAFIKRABOTY v4.9")
    log("=" * 70)
    log("")
    
    # Проверка файлов
    if not check_source_files():
        return False
    
    # Компиляция
    if not compile_installer():
        return False
    
    # Проверка
    if not verify_output():
        return False
    
    # Итог
    log("")
    log("=" * 70)
    log("✅ СБОРКА УСТАНОВЩИКА ЗАВЕРШЕНА")
    log("=" * 70)
    log("")
    log(f"📂 Установщик: {OUTPUT_DIR / '*.exe'}")
    log("")
    log("Для установки:")
    log("  1. Запустите GrafikRaboty_Setup_v4.9.exe")
    log("  2. Следуйте инструкциям мастера")
    log("  3. Настройте telegram_config.json и vk_config.json")
    log("  4. Запустите сервер")
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
