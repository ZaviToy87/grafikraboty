# -*- coding: utf-8 -*-
"""
web_config.py — Конфигурация и утилиты для веб-сервера
Поддержка Docker, PostgreSQL и переменных окружения
"""
import os
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Режим работы (Docker или локальный)
DOCKER_MODE = os.getenv('DOCKER_MODE', 'false').lower() == 'true'
USE_POSTGRES = os.getenv('DATABASE_URL', '').startswith('postgresql')

# Пути - используем app_paths для консистентности
try:
    from app_paths import DATA_DIR, DB_PATH, UPLOADS_DIR, LOGS_DIR
except ImportError:
    # Если app_paths нет (например в EXE), используем BASE_DIR
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Для Docker используем volumes
    if DOCKER_MODE:
        DATA_DIR = os.getenv('DATA_DIR', '/app/data')
        UPLOADS_DIR = os.getenv('UPLOADS_DIR', '/app/uploads')
        LOGS_DIR = os.getenv('LOGS_DIR', '/app/logs')
        DB_PATH = os.getenv('DB_PATH', '/app/data/schedule.db')
    else:
        DATA_DIR = BASE_DIR
        DB_PATH = os.path.join(DATA_DIR, 'schedule.db')
        UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
        LOGS_DIR = os.path.join(DATA_DIR, 'logs')

# Для EXE версии проверяем что директории существуют
if hasattr(sys, 'frozen') and sys.frozen:
    # Создаём директорию данных если нет
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Копируем базу данных из папки программы если её нет
    if not os.path.exists(DB_PATH):
        exe_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.db')
        if os.path.exists(exe_db):
            shutil.copy2(exe_db, DB_PATH)
else:
    # Для обычного запуска создаём директории
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    if DOCKER_MODE:
        os.makedirs(DATA_DIR, exist_ok=True)

# Логирование
logger = logging.getLogger('web_server')
logger.setLevel(logging.DEBUG)  # Максимальный уровень логирования

# File handler
_log_file = os.path.join(LOGS_DIR, 'web_server.log')
try:
    fh = logging.FileHandler(_log_file, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(fh)
    logger.info(f"Log file initialized: {_log_file}")
except Exception as e:
    logger.warning(f"Failed to setup file logging: {e}")

# Console handler - подробный формат
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:\n  %(message)s'))
logger.addHandler(ch)


def get_db_connection():
    """Создать подключение к базе данных (SQLite или PostgreSQL)"""
    if USE_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def audit_log(user_id, action, details=None):
    """Запись в audit_log"""
    from flask import request
    try:
        db = get_db_connection()
        cur = db.cursor()
        ip = request.remote_addr if request else None
        cur.execute(
            'INSERT INTO audit_log (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)',
            (user_id, action, details, ip)
        )
        db.commit()
    except Exception as e:
        logger.warning(f"audit_log error: {e}")


def send_telegram_message(chat_ids, text, token=None):
    """
    Отправить сообщение в Telegram
    Returns: (sent_count, total)
    """
    if not chat_ids:
        return 0, 0
    
    if not token:
        try:
            import json
            config_path = os.path.join(DATA_DIR, 'telegram_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            token = config.get('token')
        except:
            logger.warning("Failed to load Telegram config")
            return 0, len(chat_ids)
    
    sent = 0
    for cid in chat_ids:
        try:
            import urllib.request
            import json
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': cid,
                'text': text,
                'parse_mode': 'HTML'
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                if result.get('ok'):
                    sent += 1
                    logger.info(f"Telegram sent to {cid}")
                else:
                    logger.warning(f"Telegram error for {cid}: {result}")
        except Exception as e:
            logger.warning(f"Telegram send to {cid} failed: {e}")
    
    return sent, len(chat_ids)
