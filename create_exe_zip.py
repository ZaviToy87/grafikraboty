# -*- coding: utf-8 -*-
"""
Создание ZIP архива из EXE версии
"""
import zipfile
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
SOURCE_DIR = PROJECT_ROOT / "exe_dist" / "GrafikRaboty_Server"
OUTPUT_FILE = PROJECT_ROOT / "installer_dist" / f"GrafikRaboty_Server_EXE_v4.9_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def zip_directory():
    log(f"📦 Создание ZIP архива из {SOURCE_DIR}")
    
    if not SOURCE_DIR.exists():
        log(f"❌ Директория не найдена: {SOURCE_DIR}")
        return False
    
    # Создаём архив
    with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(SOURCE_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(SOURCE_DIR.parent)
                
                try:
                    zipf.write(file_path, arcname)
                    file_count += 1
                    total_size += file_path.stat().st_size
                except Exception as e:
                    log(f"⚠️ Ошибка добавления {file_path}: {e}")
        
        log(f"✅ Архив создан: {OUTPUT_FILE.name}")
        log(f"📊 Файлов: {file_count}")
        log(f"📊 Размер архива: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")
        log(f"📊 Исходный размер: {total_size / 1024 / 1024:.2f} MB")
    
    return True

if __name__ == '__main__':
    try:
        success = zip_directory()
        exit(0 if success else 1)
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
