# -*- coding: utf-8 -*-
"""
GrafikRaboty Server Launcher
Запуск сервера с скрытием консоли
"""
import os
import sys
import subprocess
import ctypes

# Получаем путь к текущей директории
if getattr(sys, 'frozen', False):
    # Запущен из EXE
    BASE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    # Запущен из исходников
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

# Путь к web_server.py
SERVER_SCRIPT = os.path.join(EXE_DIR, 'web_server.py')

# Меняем рабочую директорию
os.chdir(EXE_DIR)

# Скрываем консоль (для windows)
try:
    ctypes.windll.kernel32.FreeConsole()
except Exception:
    pass

# Запускаем сервер
print(f"Starting GrafikRaboty Server from: {EXE_DIR}")
print(f"Script: {SERVER_SCRIPT}")

# Создаём лог-файл
log_path = os.path.join(EXE_DIR, 'server_start.log')
with open(log_path, 'w', encoding='utf-8') as log:
    log.write(f"Starting server from: {EXE_DIR}\n")
    log.write(f"Script: {SERVER_SCRIPT}\n")
    
    try:
        # Запускаем web_server.py
        result = subprocess.run(
            [sys.executable, SERVER_SCRIPT],
            cwd=EXE_DIR,
            capture_output=True,
            text=True
        )
        log.write(f"Exit code: {result.returncode}\n")
        if result.stdout:
            log.write(f"STDOUT:\n{result.stdout}\n")
        if result.stderr:
            log.write(f"STDERR:\n{result.stderr}\n")
    except Exception as e:
        log.write(f"Error: {e}\n")
