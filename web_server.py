# -*- coding: utf-8 -*-
"""
web_server.py — Главный веб-сервер ГрафикРаботы
Модульная структура:
- web_config: конфигурация, БД, логирование
- web_auth: аутентификация, VK верификация
- web_api: API роуты
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, make_response
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os
import hashlib
import json
import secrets
import socket
import threading
import logging

# Импорт модулей
from web_config import logger, get_db_connection, audit_log, send_telegram_message, DATA_DIR, DB_PATH, UPLOADS_DIR, LOGS_DIR
from web_auth import auth_bp
from web_api import api_bp
from web_chat import chat_bp
from web_work_journal import wj_bp
from web_barcodes import barcodes_bp
from web_converter import converter_bp
from web_admin import admin_bp
from web_vk_chat import vk_chat_bp
from web_revision import revision_bp
from web_reminders import reminders_bp
from web_com_scanner import com_scanner_bp
from web_products_1c import products_1c_bp
from smart_revision_system import smart_bp
from web_notifications import notifications_bp, create_notifications_table, init_socketio
from web_analytics import analytics_bp
from web_export import export_bp
from web_sync_1c import sync_1c_bp



# Запуск VK бота для получения сообщений
try:
    import vk_bot
    import threading
    # Создаём директорию для логов vk_bot
    vk_log_dir = os.path.join(DATA_DIR, 'logs')
    os.makedirs(vk_log_dir, exist_ok=True)
    vk_thread = threading.Thread(target=lambda: vk_bot.start_polling(), daemon=True)
    vk_thread.start()
    logger.info("VK bot started")
except Exception as e:
    logger.warning(f"VK bot not started: {e}")

# Запуск планировщика ревизии товаров
try:
    from scheduler_revision import start_scheduler
    start_scheduler()
    logger.info("Revision scheduler started")
except Exception as e:
    logger.warning(f"Revision scheduler not started: {e}")

# Запуск COM-сканеров штрих-кодов
# ТЕПЕРЬ НЕ ЗАПУСКАЮТСЯ АВТОМАТИЧЕСКИ — пользователь включает кнопкой в интерфейсе
try:
    from com_scanner import get_scanners_status
    logger.info("COM scanners initialized (disabled by default - user can enable in UI)")
except Exception as e:
    logger.warning(f"COM scanners not initialized: {e}")

# Инициализация Flask
app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'grafikraboty-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB
app.config['SESSION_COOKIE_SECURE'] = False  # Разрешить куки по HTTP (для localhost)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Защита от XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Разрешить куки при редиректах

# Socket.IO - без async_mode (автоматический выбор)
# PyInstaller должен включить simple-websocket
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    manage_session=False,
    allow_upgrades=True  # Разрешить переход с polling на websocket
)

# Регистрация blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(wj_bp, url_prefix='/api/work-journal')
app.register_blueprint(barcodes_bp, url_prefix='/api/barcodes')
app.register_blueprint(converter_bp)
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(vk_chat_bp, url_prefix='/api/vk-chat')
app.register_blueprint(revision_bp, url_prefix='/api/revision')
app.register_blueprint(reminders_bp, url_prefix='/api/reminders')
app.register_blueprint(com_scanner_bp, url_prefix='/api/com-scanner')
app.register_blueprint(products_1c_bp, url_prefix='/api/products-1c')
app.register_blueprint(smart_bp, url_prefix='/api/smart')
app.register_blueprint(notifications_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(export_bp)
app.register_blueprint(sync_1c_bp)


# Создание таблицы уведомлений при старте
create_notifications_table()

# Инициализация Socket.IO для уведомлений
init_socketio(socketio)


# ==========================================
# Основные роуты
# ==========================================

@app.route('/')
def index():
    """Редирект на dashboard или login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))


@app.route('/dashboard')
def dashboard():
    """Главная страница - календарь"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html',
                         user={
                             'username': session.get('username'),
                             'full_name': session.get('full_name'),
                             'role': session.get('role')
                         },
                         app_version='20260324_v3')  # Версия для кэша JS


@app.route('/chat')
def chat_page():
    """Страница VK чата"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('chat.html')


@app.route('/recipes')
def recipes_page():
    """Страница рецептов"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('recipes.html')


@app.route('/sync-1c')
def sync_1c_page():
    """Страница просмотра данных из 1С"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('sync_1c.html',
                         user={
                             'username': session.get('username'),
                             'full_name': session.get('full_name'),
                             'role': session.get('role')
                         })


@app.route('/sync-1c/daily')
def sync_1c_daily_page():
    """Страница аналитики продаж и приемок по дням"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('sync_1c_daily.html')


@app.route('/sync-1c/analytics')
def sync_1c_analytics_page():
    """Страница полной аналитики 1С"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('sync_1c_analytics.html')


@app.route('/api/drugs/import', methods=['POST'])

def import_drugs():
    """Импорт препаратов из файла"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не загружен'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    # Сохранение файла
    upload_dir = 'uploads/drugs'
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, secure_filename(file.filename))
    file.save(file_path)
    
    try:
        # Импорт препаратов
        import import_drugs_from_excel
        import_drugs_from_excel.create_drugs_table()
        
        # Определение типа файла
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.xls', '.xlsx']:
            drugs = import_drugs_from_excel.parse_excel_file(file_path)
        elif file_ext == '.csv':
            drugs = import_drugs_from_excel.parse_csv_file(file_path)
        else:
            return jsonify({'error': f'Неподдерживаемый формат файла: {file_ext}'}), 400
        
        if not drugs:
            return jsonify({'error': 'Не удалось извлечь данные из файла'}), 400
        
        # Сохранение в базу данных
        saved_count = import_drugs_from_excel.save_drugs_to_db(drugs)
        
        # Экспорт в JSON для фронтенда
        import_drugs_from_excel.export_drugs_to_json()
        
        return jsonify({
            'success': True,
            'message': f'Импорт завершен успешно',
            'processed': len(drugs),
            'saved': saved_count
        })
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при импорте: {str(e)}'}), 500

@app.route('/api/drugs/list')
def get_drugs_list():
    """Получение списка препаратов для фронтенда"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        # Чтение из JSON файла
        json_path = 'static/data/drugs.json'
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                drugs = json.load(f)
        else:
            # Если файла нет, возвращаем пустой список
            drugs = []
        
        return jsonify({'drugs': drugs})
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при чтении данных: {str(e)}'}), 500


@app.route('/test-scanner')
def test_scanner():
    """Страница теста COM-сканера штрих-кодов"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('test_scanner.html')


@app.route('/login')
def login_page():
    """Страница входа (рендер)"""
    return render_template('login.html')


@app.route('/favicon.ico')
def favicon():
    """Favicon"""
    return '', 204


# ==========================================
# Socket.IO события
# ==========================================

@socketio.on('connect')
def handle_connect():
    """Клиент подключился"""
    logger.info(f"WebSocket connected: {request.sid if request else 'unknown'}")


@socketio.on('disconnect')
def handle_disconnect():
    """Клиент отключился"""
    logger.info(f"WebSocket disconnected: {request.sid if request else 'unknown'}")


@socketio.on('join')
def handle_join(data):
    """Клиент присоединяется к комнате пользователя для уведомлений"""
    user_id = data.get('user_id')
    if user_id:
        room = f'user_{user_id}'
        emit('joined', {'room': room})
        logger.info(f"User {user_id} joined room {room}")


@socketio.on('schedule_updated')
def handle_schedule_updated(data):
    """График обновлён - уведомить клиентов"""
    emit('schedule_updated', data, broadcast=True)



# ==========================================
# Вспомогательные функции
# ==========================================

def init_db():
    """Инициализация БД если пуста"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            return  # Таблицы уже есть
        
        # Создаём таблицы
        cursor.execute('PRAGMA foreign_keys = ON')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#3498db',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                task_ids TEXT DEFAULT '[]',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, year, month, day)
            )
        ''')
        
        # Индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedule_user_date ON schedule(user_id, year, month, day)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedule(year, month, day)')
        
        # Пользователи по умолчанию
        admins = [
            ('admin', 'admin', 'Администратор (Юлия и Денис)'),
        ]
        employees = [
            ('валерия', 'pass123', 'Валерия Сотрудник'),
            ('ольга', 'pass456', 'Ольга Сотрудник')
        ]
        
        for username, password, full_name in admins + employees:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            role = 'admin' if username == 'admin' else 'employee'
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)',
                    (username, password_hash, role, full_name)
                )
            except:
                pass
        
        # Задачи по умолчанию
        default_tasks = [
            ('Протирка полок', '#B39DDB'),
            ('Уборка влажная', '#4CAF50'),
            ('Проверка ценников', '#FFEB3B'),
            ('Сроки годности, Акции', '#4CAF50'),
            ('Ревизия', '#2196F3'),
            ('Смена физическая', '#E91E63'),
            ('Отпуск', '#E74C3C'),
            ('Больничный', '#95A5A6'),
            ('Выходной', '#BDC3C7')
        ]
        
        for task_name, color in default_tasks:
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO tasks (name, color) VALUES (?, ?)',
                    (task_name, color)
                )
            except:
                pass
        
        db.commit()
        logger.info("Database initialized")
    except Exception as e:
        logger.exception(f"Database init error: {e}")


# ==========================================
# Запуск сервера
# ==========================================

def run_server(host='0.0.0.0', port=8080, debug=False):
    """Запустить веб-сервер"""
    init_db()
    logger.info(f"Starting web server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, log_output=False)


if __name__ == '__main__':
    run_server()
