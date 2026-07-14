# server.py - Серверная часть приложения
import socket
import threading
import sqlite3
import json
import os
import hashlib
import time
from datetime import datetime
import logging
from pathlib import Path
import base64
import subprocess
import shutil

try:
    from app_paths import DB_PATH as _DB_PATH, SERVER_LOG_PATH, UPLOADS_DIR
    from app_paths import ensure_uploads_dir
except ImportError:
    _DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedule.db')
    SERVER_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log')
    UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    def ensure_uploads_dir():
        os.makedirs(UPLOADS_DIR, exist_ok=True)

class ScheduleServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server = None
        self.clients = {}
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(SERVER_LOG_PATH),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """Создание и настройка базы данных"""
        try:
            self.db = sqlite3.connect(_DB_PATH, check_same_thread=False)
            self.db.row_factory = sqlite3.Row
            # Включаем проверку внешних ключей
            self.db.execute('PRAGMA foreign_keys = ON')
            self.create_tables()
            self.logger.info("База данных подключена успешно")
        except Exception as e:
            self.logger.error(f"Критическая ошибка при подключении к БД: {e}")
            raise
        
    def create_tables(self):
        """Создание таблиц в БД"""
        cursor = self.db.cursor()
        
        # Пользователи
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
        
        # Задачи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#3498db' CHECK(color GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]'),
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
        
        # График работы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 2020 AND year <= 2100),
                month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
                day INTEGER NOT NULL CHECK(day >= 1 AND day <= 31),
                task_ids TEXT DEFAULT '[]',  -- JSON список ID задач
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, year, month, day)
            )
        ''')
        
        # Загруженные файлы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 2020 AND year <= 2100),
                month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
                day INTEGER NOT NULL CHECK(day >= 1 AND day <= 31),
                file_type TEXT,
                file_size INTEGER DEFAULT 0 CHECK(file_size >= 0),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Журнал действий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Сообщения чата
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                full_name TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Создаем индексы для улучшения производительности
        self.create_indexes(cursor)
        
        self.db.commit()
        self.logger.info("База данных инициализирована успешно")
        
        # Миграция: добавить колонки в schedule, если их нет (старые БД)
        self._migrate_schedule_columns(cursor)
        self.db.commit()
        
        # Миграция: чат с темами и задачи коллегам
        self._migrate_chat_and_colleague_tables()
        
        # Проверяем целостность базы данных
        self.verify_database_integrity()
        
        # Создаем администраторов по умолчанию
        self.create_default_users()
    
    def create_indexes(self, cursor):
        """Создание индексов для оптимизации запросов"""
        try:
            # Индексы для таблицы schedule
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedule_user_date ON schedule(user_id, year, month, day)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedule(year, month, day)')
            
            # Индексы для таблицы files
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_user_date ON files(user_id, year, month, day)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_date ON files(year, month, day)')
            
            # Индексы для таблицы audit_log
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_log(created_at)')
            
            # Индексы для таблицы chat_messages
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_date ON chat_messages(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id)')
            
            # Индексы для таблицы tasks
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by)')
            
            self.logger.info("Индексы базы данных созданы успешно")
        except Exception as e:
            self.logger.error(f"Ошибка при создании индексов: {e}")
    
    def _migrate_schedule_columns(self, cursor):
        """Добавить колонки created_at/updated_at в schedule, если их нет (совместимость со старыми БД)."""
        try:
            cursor.execute('PRAGMA table_info(schedule)')
            columns = [row[1] for row in cursor.fetchall()]
            if 'created_at' not in columns:
                cursor.execute('ALTER TABLE schedule ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                self.logger.info("Миграция: добавлена колонка schedule.created_at")
            if 'updated_at' not in columns:
                cursor.execute('ALTER TABLE schedule ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                self.logger.info("Миграция: добавлена колонка schedule.updated_at")
        except Exception as e:
            self.logger.warning(f"Миграция schedule: {e}")
    
    def _migrate_chat_and_colleague_tables(self):
        """Таблицы тем чата и задач коллегам (совместимость с веб-версией)."""
        cursor = self.db.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_topics'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE chat_topics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users(id)
                    )
                ''')
                cursor.execute("INSERT INTO chat_topics (id, title) VALUES (1, 'Общий')")
                self.logger.info("Миграция: создана таблица chat_topics")
            try:
                cursor.execute("SELECT topic_id FROM chat_messages LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN topic_id INTEGER DEFAULT 1")
                self.logger.info("Миграция: добавлена колонка chat_messages.topic_id")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='colleague_tasks'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE colleague_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_by INTEGER NOT NULL,
                        assignee_id INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        month INTEGER NOT NULL,
                        day INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        color TEXT DEFAULT '#3498db',
                        file_id INTEGER,
                        completed INTEGER DEFAULT 0,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users(id),
                        FOREIGN KEY (assignee_id) REFERENCES users(id)
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_colleague_tasks_date ON colleague_tasks(year, month, day)')
                self.logger.info("Миграция: создана таблица colleague_tasks")
            
            # Миграция: таблица штрих-кодов (barcodes)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='barcodes'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE barcodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_name TEXT NOT NULL,
                        factory_barcode TEXT,
                        internal_barcode TEXT,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active INTEGER DEFAULT 1,
                        FOREIGN KEY (created_by) REFERENCES users(id)
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcodes_internal ON barcodes(internal_barcode)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcodes_factory ON barcodes(factory_barcode)')
                self.logger.info("Миграция: создана таблица barcodes")
            
            self.db.commit()
        except Exception as e:
            self.logger.warning(f"Миграция chat/colleague/barcodes: {e}")

    def verify_database_integrity(self):
        """Проверка целостности базы данных"""
        try:
            cursor = self.db.cursor()
            
            # Проверяем целостность внешних ключей
            cursor.execute('PRAGMA foreign_key_check')
            issues = cursor.fetchall()
            if issues:
                self.logger.warning(f"Обнаружены проблемы целостности БД: {len(issues)} записей")
            else:
                self.logger.info("Целостность базы данных проверена успешно")
            
            # Проверяем количество записей в основных таблицах
            tables = ['users', 'tasks', 'schedule', 'files', 'audit_log', 'chat_messages', 'barcodes']
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                count = cursor.fetchone()['count']
                self.logger.info(f"Таблица {table}: {count} записей")
                
        except Exception as e:
            self.logger.error(f"Ошибка при проверке целостности БД: {e}")
        
    def create_default_users(self):
        """Создание администраторов по умолчанию"""
        cursor = self.db.cursor()
        
        # Администраторы
        admins = [
            # Общий админ-аккаунт для Юлии и Дениса
            ('admin', 'admin', 'Администратор (Юлия и Денис)'),
        ]
        
        # Сотрудники
        employees = [
            ('валерия', 'pass123', 'Валерия Сотрудник'),
            ('ольга', 'pass456', 'Ольга Сотрудник')
        ]
        
        for username, password, full_name in admins:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, password_hash, role, full_name)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, 'admin', full_name))
            except:
                pass
                
        for username, password, full_name in employees:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, password_hash, role, full_name)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, 'employee', full_name))
            except:
                pass
                
        # Создаем базовые задачи (Протирка полок — сереневый, сб/вс)
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
                cursor.execute('''
                    INSERT OR IGNORE INTO tasks (name, color)
                    VALUES (?, ?)
                ''', (task_name, color))
            except:
                pass
                
        self.db.commit()
        
    def start(self):
        """Запуск сервера"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        
        self.logger.info(f"Сервер запущен на {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, client_address = self.server.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.start()
        except KeyboardInterrupt:
            self.logger.info("Остановка сервера...")
            self.stop()
            
    def handle_client(self, client_socket, client_address):
        """Обработка клиентского соединения"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.logger.info(f"Новое подключение: {client_id}")

        try:
            while True:
                # Увеличиваем буфер для больших запросов (например, с файлами)
                raw_data = client_socket.recv(1048576)  # 1MB буфер
                if not raw_data:
                    break

                # Проверяем первые байты - если не текст, отключаем клиента
                # Валидное JSON начинается с {, [, " или пробельных символов
                stripped = raw_data.lstrip()
                if not stripped or stripped[0] not in (ord('{'), ord('['), ord('"'), ord(' ')):
                    self.logger.warning(f"Некорректные данные от {client_id}: первые байты {raw_data[:8].hex()}")
                    break

                try:
                    data = raw_data.decode('utf-8')
                except UnicodeDecodeError as e:
                    self.logger.warning(f"Ошибка декодирования UTF-8 от {client_id}: {e}")
                    break

                try:
                    request = json.loads(data)
                    response = self.process_request(request, client_address[0])

                    # Отправляем ответ
                    response_json = json.dumps(response)
                    client_socket.send(response_json.encode('utf-8'))
                except json.JSONDecodeError as e:
                    self.logger.error(f"Ошибка парсинга JSON: {e}, данные: {data[:100]}")
                    error_response = {'status': 'error', 'message': f'Некорректный JSON: {str(e)}'}
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                except Exception as e:
                    self.logger.exception("Ошибка при обработке запроса")
                    error_response = {'status': 'error', 'message': f'Ошибка сервера: {str(e)}'}
                    client_socket.send(json.dumps(error_response).encode('utf-8'))

        except ConnectionResetError:
            self.logger.info(f"Соединение разорвано: {client_id}")
        finally:
            client_socket.close()
            
    def process_request(self, request, ip_address):
        """Обработка запроса от клиента с проверками валидности"""
        # Проверка валидности запроса
        if not isinstance(request, dict):
            self.logger.error(f"Некорректный тип запроса: {type(request)}")
            return {'status': 'error', 'message': 'Некорректный формат запроса'}
        
        action = request.get('action')
        if not action:
            self.logger.error("Запрос не содержит поля 'action'")
            return {'status': 'error', 'message': 'Отсутствует поле action'}
        
        # Логируем действие для отладки
        self.logger.info(f"Обработка действия: {action} от IP: {ip_address}")
        
        if action == 'login':
            return self.handle_login(request, ip_address)
        elif action == 'get_schedule':
            return self.get_schedule(request)
        elif action == 'update_schedule':
            return self.update_schedule(request)
        elif action == 'upload_file':
            return self.handle_file_upload(request)
        elif action == 'get_files':
            return self.get_files(request)
        elif action == 'get_users':
            return self.get_users(request)
        elif action == 'add_task':
            return self.add_task(request)
        elif action == 'update_task':
            return self.update_task(request)
        elif action == 'delete_task':
            return self.delete_task(request)
        elif action == 'get_tasks':
            return self.get_tasks()
        elif action == 'get_audit_log':
            return self.get_audit_log(request)
        elif action == 'download_file':
            return self.download_file(request)
        elif action == 'send_chat_message':
            return self.send_chat_message(request)
        elif action == 'get_chat_messages':
            return self.get_chat_messages(request)
        elif action == 'get_chat_topics':
            return self.get_chat_topics(request)
        elif action == 'create_chat_topic':
            return self.create_chat_topic(request)
        elif action == 'update_chat_topic':
            return self.update_chat_topic(request)
        elif action == 'edit_chat_message':
            return self.edit_chat_message(request)
        elif action == 'delete_chat_message':
            return self.delete_chat_message(request)
        elif action == 'get_colleagues':
            return self.get_colleagues(request)
        elif action == 'get_colleague_tasks':
            return self.get_colleague_tasks(request)
        elif action == 'create_colleague_task':
            return self.create_colleague_task(request)
        elif action == 'complete_colleague_task':
            return self.complete_colleague_task(request)
        elif action == 'add_user':
            return self.add_user(request, ip_address)
        elif action == 'update_user':
            return self.update_user(request, ip_address)
        elif action == 'delete_user':
            return self.delete_user(request, ip_address)
        elif action == 'get_system_stats':
            return self.get_system_stats(request)
        elif action == 'delete_file':
            return self.delete_file(request, ip_address)
        elif action == 'system_update':
            return self.handle_system_update(request, ip_address)
        else:
            self.logger.warning(f"Неизвестное действие: {action}")
            return {'status': 'error', 'message': f'Неизвестное действие: {action}'}
            
    def handle_login(self, request, ip_address):
        """Обработка входа в систему с проверками валидности"""
        username = request.get('username', '').strip().lower()
        password = request.get('password', '')
        
        # Валидация входных данных
        if not username or not password:
            self.logger.warning(f"Попытка входа с пустыми полями от IP: {ip_address}")
            return {'status': 'error', 'message': 'Введите логин и пароль'}
        
        if len(username) > 100:
            self.logger.warning(f"Слишком длинный логин от IP: {ip_address}")
            return {'status': 'error', 'message': 'Логин слишком длинный (максимум 100 символов)'}
        
        if len(password) > 200:
            self.logger.warning(f"Слишком длинный пароль от IP: {ip_address}")
            return {'status': 'error', 'message': 'Пароль слишком длинный'}
        
        cursor = self.db.cursor()
        cursor.execute(
            'SELECT id, username, password_hash, role, full_name FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        
        if user:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user['password_hash'] == password_hash:
                # Логируем успешный вход
                self.log_audit(
                    user['id'],
                    'login',
                    f'Успешный вход с IP {ip_address}',
                    ip_address
                )
                
                return {
                    'status': 'success',
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role'],
                        'full_name': user['full_name']
                    }
                }
                
        # Логируем неудачную попытку
        self.log_audit(
            None,
            'failed_login',
            f'Неудачная попытка входа для пользователя {username}',
            ip_address
        )
        
        return {'status': 'error', 'message': 'Неверные учетные данные'}
        
    def get_schedule(self, request):
        """Получение графика"""
        user_id = request.get('user_id')
        year = request.get('year')
        month = request.get('month')
        
        cursor = self.db.cursor()
        
        if request.get('role') == 'admin':
            # Администраторы видят всех
            cursor.execute('''
                SELECT s.*, u.full_name 
                FROM schedule s
                JOIN users u ON s.user_id = u.id
                WHERE s.year = ? AND s.month = ?
                ORDER BY s.day, u.full_name
            ''', (year, month))
        else:
            # Сотрудники видят только себя
            cursor.execute('''
                SELECT * FROM schedule 
                WHERE user_id = ? AND year = ? AND month = ?
                ORDER BY day
            ''', (user_id, year, month))
            
        schedule_data = cursor.fetchall()
        result = [dict(row) for row in schedule_data]
        try:
            import recurring_schedule
            recurring = recurring_schedule.get_recurring_for_month(int(year), int(month))
        except Exception:
            recurring = []
        return {'status': 'success', 'schedule': result, 'recurring': recurring}
        
    def update_schedule(self, request):
        """Обновление графика"""
        user_id = request.get('user_id')
        year = request.get('year')
        month = request.get('month')
        day = request.get('day')
        task_ids = json.dumps(request.get('task_ids', []))
        notes = request.get('notes', '')
        
        cursor = self.db.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO schedule 
                (user_id, year, month, day, task_ids, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, year, month, day, task_ids, notes))
            
            self.db.commit()
            
            # Логируем изменение
            self.log_audit(
                user_id,
                'update_schedule',
                f'Обновлен график на {day}.{month}.{year}',
                request.get('ip_address', '')
            )
            
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def handle_file_upload(self, request):
        """Обработка загрузки файла"""
        user_id = request.get('user_id')
        filename = request.get('filename')
        file_data = request.get('file_data')  # Base64 encoded string
        if not filename or not file_data:
            return {'status': 'error', 'message': 'Нет данных файла'}

        try:
            ensure_uploads_dir()
            upload_dir = Path(UPLOADS_DIR)

            # Генерируем уникальное имя файла
            unique_filename = f"{int(time.time())}_{filename}"
            filepath = upload_dir / unique_filename

            # Декодируем base64 и сохраняем файл на диск
            raw_bytes = base64.b64decode(file_data.encode('utf-8'))
            with open(filepath, 'wb') as f:
                f.write(raw_bytes)

            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO files 
                (filename, filepath, user_id, year, month, day, file_type, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, 
                str(filepath), 
                user_id,
                request.get('year'),
                request.get('month'),
                request.get('day'),
                request.get('file_type'),
                request.get('file_size', 0)
            ))
            
            self.db.commit()
            
            # Логируем загрузку
            self.log_audit(
                user_id,
                'upload_file',
                f'Загружен файл {filename}',
                request.get('ip_address', '')
            )
            
            return {'status': 'success', 'filename': unique_filename}
        except Exception as e:
            self.logger.exception("Ошибка при сохранении файла")
            return {'status': 'error', 'message': f'Ошибка сохранения файла: {e}'}

    def handle_system_update(self, request, ip_address):
        """Обработка обновления системы"""
        user_id = request.get('user_id')
        role = request.get('role')
        file_name = request.get('file_name')
        file_data = request.get('file_data')
        file_size = request.get('file_size', 0)
        
        # Проверка прав доступа
        if role != 'admin':
            self.logger.warning(f"Попытка обновления от не-админа: {user_id}")
            return {'status': 'error', 'message': 'Требуется права администратора'}
        
        if not file_name or not file_data:
            return {'status': 'error', 'message': 'Нет данных файла'}
        
        try:
            self.logger.info(f"Начало обновления системы. Файл: {file_name}, размер: {file_size} байт")
            
            # Создаем директорию для обновлений
            update_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'updates')
            os.makedirs(update_dir, exist_ok=True)
            
            # Путь для сохранения файла обновления
            unique_filename = f"update_{int(time.time())}_{file_name}"
            update_file_path = os.path.join(update_dir, unique_filename)
            
            # Декодируем и сохраняем файл
            raw_bytes = base64.b64decode(file_data.encode('utf-8'))
            with open(update_file_path, 'wb') as f:
                f.write(raw_bytes)
            
            self.logger.info(f"Файл обновления сохранен: {update_file_path}")
            
            # Логируем обновление
            self.log_audit(
                user_id,
                'system_update',
                f'Загружено обновление: {file_name}',
                ip_address
            )
            
            # Запускаем процесс установки обновления в отдельном потоке
            def install_update():
                try:
                    time.sleep(2)  # Небольшая задержка для отправки ответа

                    self.logger.info("Начало установки обновления...")

                    # Путь к скрипту установщика
                    installer_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_installer.py')

                    # Если скрипт установщика существует, запускаем его
                    if os.path.exists(installer_script):
                        # Запускаем установщик
                        subprocess.Popen(
                            ['python', installer_script, update_file_path],
                            creationflags=subprocess.DETACHED_PROCESS,
                            close_fds=True
                        )
                        self.logger.info("Запущен скрипт установки обновления")
                        
                        # Закрываем сервер после запуска установщика
                        self.logger.info("Сервер закрывается для установки обновления...")
                        self.stop()
                        os._exit(0)  # Завершаем процесс сервера
                    else:
                        # Если скрипта нет, просто копируем файл
                        self.logger.warning("Скрипт update_installer.py не найден. Копирование файла...")
                        target_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'График.exe')
                        shutil.copy2(update_file_path, target_exe)
                        self.logger.info(f"Файл скопирован в {target_exe}")

                except Exception as e:
                    self.logger.exception(f"Ошибка при установке обновления: {e}")

            # Запускаем установку в отдельном потоке
            update_thread = threading.Thread(target=install_update, daemon=True)
            update_thread.start()

            return {
                'status': 'success',
                'message': 'Обновление загружено и устанавливается. Сервер будет перезапущен.',
                'filename': unique_filename
            }
            
        except Exception as e:
            self.logger.exception("Ошибка при обработке обновления")
            return {'status': 'error', 'message': f'Ошибка обновления: {e}'}

    def get_files(self, request):
        """Получение списка файлов"""
        year = request.get('year')
        month = request.get('month')
        day = request.get('day')
        role = request.get('role')
        
        cursor = self.db.cursor()
        
        # Если админ и не указан день - возвращаем все файлы
        if role == 'admin' and not day:
            cursor.execute('''
                SELECT f.*, u.full_name 
                FROM files f
                JOIN users u ON f.user_id = u.id
                ORDER BY f.uploaded_at DESC
                LIMIT 1000
            ''')
        elif role == 'admin' and day:
            cursor.execute('''
                SELECT f.*, u.full_name 
                FROM files f
                JOIN users u ON f.user_id = u.id
                WHERE f.year = ? AND f.month = ? AND f.day = ?
                ORDER BY f.uploaded_at DESC
            ''', (year, month, day))
        else:
            if day:
                cursor.execute('''
                    SELECT * FROM files 
                    WHERE user_id = ? AND year = ? AND month = ? AND day = ?
                    ORDER BY uploaded_at DESC
                ''', (request.get('user_id'), year, month, day))
            else:
                cursor.execute('''
                    SELECT * FROM files 
                    WHERE user_id = ?
                    ORDER BY uploaded_at DESC
                    LIMIT 1000
                ''', (request.get('user_id'),))
            
        files = cursor.fetchall()
        
        result = []
        for file in files:
            result.append(dict(file))
            
        return {'status': 'success', 'files': result}
    
    def delete_file(self, request, ip_address):
        """Удаление файла"""
        file_id = request.get('file_id')
        user_id = request.get('user_id')
        role = request.get('role')
        
        if not file_id:
            return {'status': 'error', 'message': 'Не указан ID файла'}
        
        try:
            cursor = self.db.cursor()
            
            # Проверяем доступ к файлу
            if role == 'admin':
                cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
            else:
                cursor.execute('SELECT * FROM files WHERE id = ? AND user_id = ?', (file_id, user_id))
            
            file = cursor.fetchone()
            
            if not file:
                return {'status': 'error', 'message': 'Файл не найден или доступ запрещен'}
            
            # Удаляем файл с диска
            try:
                filepath = Path(file['filepath'])
                if filepath.exists():
                    filepath.unlink()
            except Exception as e:
                self.logger.warning(f"Не удалось удалить файл с диска: {e}")
            
            # Удаляем запись из БД
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            self.db.commit()
            
            self.log_audit(
                user_id,
                'delete_file',
                f'Удален файл ID={file_id}: {file["filename"]}',
                ip_address
            )
            
            return {'status': 'success'}
        except Exception as e:
            self.logger.exception("Ошибка при удалении файла")
            return {'status': 'error', 'message': f'Ошибка удаления файла: {str(e)}'}
        
    def get_users(self, request):
        """Получение списка пользователей. Админ — все, сотрудник — для выбора коллег."""
        if not request.get('user_id'):
            return {'status': 'error', 'message': 'Не авторизован'}
        cursor = self.db.cursor()
        cursor.execute('SELECT id, username, role, full_name FROM users ORDER BY role, full_name')
        users = cursor.fetchall()
        result = [dict(u) for u in users]
        return {'status': 'success', 'users': result}
        
    def add_task(self, request):
        """Добавление новой задачи (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}
            
        task_name = request.get('task_name')
        color = request.get('color', '#FFFFFF')
        
        cursor = self.db.cursor()
        cursor.execute(
            'INSERT INTO tasks (name, color, created_by) VALUES (?, ?, ?)',
            (task_name, color, request.get('user_id'))
        )
        
        # Получаем ID созданной задачи
        task_id = cursor.lastrowid
        
        self.db.commit()
        
        # Логируем добавление задачи
        self.log_audit(
            request.get('user_id'),
            'add_task',
            f'Добавлена новая задача: {task_name}',
            request.get('ip_address', '')
        )
        
        return {
            'status': 'success',
            'task_id': task_id,
            'task': {
                'id': task_id,
                'name': task_name,
                'color': color
            }
        }

    def update_task(self, request):
        """Обновление существующей задачи (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}

        task_id = request.get('task_id')
        name = request.get('task_name')
        color = request.get('color')

        if not task_id or not name:
            return {'status': 'error', 'message': 'Не указан идентификатор или название задачи'}

        cursor = self.db.cursor()
        cursor.execute(
            'UPDATE tasks SET name = ?, color = ? WHERE id = ?',
            (name, color, task_id)
        )
        self.db.commit()

        self.log_audit(
            request.get('user_id'),
            'update_task',
            f'Обновлена задача id={task_id}, name={name}',
            request.get('ip_address', '')
        )

        return {'status': 'success'}

    def delete_task(self, request):
        """Удаление задачи (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}

        task_id = request.get('task_id')
        if not task_id:
            return {'status': 'error', 'message': 'Не указан идентификатор задачи'}

        cursor = self.db.cursor()

        # Удаляем задачу из таблицы tasks
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

        # Удаляем ссылку на задачу из расписания (убираем id из JSON-списков)
        cursor.execute('SELECT id, task_ids FROM schedule WHERE task_ids IS NOT NULL')
        rows = cursor.fetchall()
        for row in rows:
            try:
                task_ids = json.loads(row['task_ids'] or '[]')
            except Exception:
                task_ids = []
            new_ids = [tid for tid in task_ids if tid != task_id]
            if new_ids != task_ids:
                cursor.execute(
                    'UPDATE schedule SET task_ids = ? WHERE id = ?',
                    (json.dumps(new_ids), row['id'])
                )

        self.db.commit()

        self.log_audit(
            request.get('user_id'),
            'delete_task',
            f'Удалена задача id={task_id}',
            request.get('ip_address', '')
        )

        return {'status': 'success'}
        
    def get_tasks(self):
        """Получение списка всех задач"""
        cursor = self.db.cursor()
        cursor.execute('SELECT id, name, color FROM tasks ORDER BY name')
        tasks = cursor.fetchall()
        
        result = []
        for task in tasks:
            result.append(dict(task))
            
        return {'status': 'success', 'tasks': result}
        
    def get_audit_log(self, request):
        """Получение журнала аудита (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}
            
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT a.*, u.username 
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT 100
        ''')
        
        logs = cursor.fetchall()
        result = []
        for log in logs:
            result.append(dict(log))
            
        return {'status': 'success', 'logs': result}
    
    def add_user(self, request, ip_address):
        """Добавление нового пользователя (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}
        
        username = request.get('username', '').strip().lower()
        password = request.get('password', '')
        full_name = request.get('full_name', '').strip()
        user_role = request.get('user_role', 'employee')
        
        # Валидация
        if not username or not password or not full_name:
            return {'status': 'error', 'message': 'Заполните все обязательные поля'}
        
        if len(username) < 3:
            return {'status': 'error', 'message': 'Логин должен содержать минимум 3 символа'}
        
        if len(password) < 6:
            return {'status': 'error', 'message': 'Пароль должен содержать минимум 6 символов'}
        
        if user_role not in ['admin', 'employee']:
            return {'status': 'error', 'message': 'Неверная роль'}
        
        try:
            cursor = self.db.cursor()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, user_role, full_name))
            
            self.db.commit()
            user_id = cursor.lastrowid
            
            self.log_audit(
                request.get('user_id'),
                'add_user',
                f'Добавлен пользователь: {username} ({full_name})',
                ip_address
            )
            
            return {'status': 'success', 'user_id': user_id}
        except sqlite3.IntegrityError:
            return {'status': 'error', 'message': 'Пользователь с таким логином уже существует'}
        except Exception as e:
            self.logger.exception("Ошибка при добавлении пользователя")
            return {'status': 'error', 'message': f'Ошибка добавления пользователя: {str(e)}'}
    
    def update_user(self, request, ip_address):
        """Обновление пользователя (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}
        
        user_id = request.get('target_user_id')
        if not user_id:
            return {'status': 'error', 'message': 'Не указан ID пользователя'}
        
        try:
            cursor = self.db.cursor()
            updates = []
            values = []
            
            if 'full_name' in request:
                updates.append('full_name = ?')
                values.append(request['full_name'].strip())
            
            if 'user_role' in request:
                role = request['user_role']
                if role not in ['admin', 'employee']:
                    return {'status': 'error', 'message': 'Неверная роль'}
                updates.append('role = ?')
                values.append(role)
            
            if 'password' in request and request['password']:
                if len(request['password']) < 6:
                    return {'status': 'error', 'message': 'Пароль должен содержать минимум 6 символов'}
                password_hash = hashlib.sha256(request['password'].encode()).hexdigest()
                updates.append('password_hash = ?')
                values.append(password_hash)
            
            if not updates:
                return {'status': 'error', 'message': 'Нет данных для обновления'}
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            self.db.commit()
            
            self.log_audit(
                request.get('user_id'),
                'update_user',
                f'Обновлен пользователь ID={user_id}',
                ip_address
            )
            
            return {'status': 'success'}
        except Exception as e:
            self.logger.exception("Ошибка при обновлении пользователя")
            return {'status': 'error', 'message': f'Ошибка обновления пользователя: {str(e)}'}
    
    def delete_user(self, request, ip_address):
        """Удаление пользователя (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}
        
        user_id = request.get('target_user_id')
        if not user_id:
            return {'status': 'error', 'message': 'Не указан ID пользователя'}
        
        # Нельзя удалить самого себя
        if user_id == request.get('user_id'):
            return {'status': 'error', 'message': 'Нельзя удалить самого себя'}
        
        try:
            cursor = self.db.cursor()
            
            # Получаем информацию о пользователе для лога
            cursor.execute('SELECT username, full_name FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {'status': 'error', 'message': 'Пользователь не найден'}
            
            # Удаляем пользователя (каскадное удаление обработается БД)
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.db.commit()
            
            self.log_audit(
                request.get('user_id'),
                'delete_user',
                f'Удален пользователь: {user["username"]} ({user["full_name"]})',
                ip_address
            )
            
            return {'status': 'success'}
        except Exception as e:
            self.logger.exception("Ошибка при удалении пользователя")
            return {'status': 'error', 'message': f'Ошибка удаления пользователя: {str(e)}'}
    
    def get_system_stats(self, request):
        """Получение системной статистики (только для админов)"""
        if request.get('role') != 'admin':
            return {'status': 'error', 'message': 'Доступ запрещен'}
        
        try:
            cursor = self.db.cursor()
            
            # Количество пользователей
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            # Количество записей в графике
            cursor.execute('SELECT COUNT(*) as count FROM schedule')
            total_entries = cursor.fetchone()['count']
            
            # Количество файлов
            cursor.execute('SELECT COUNT(*) as count FROM files')
            total_files = cursor.fetchone()['count']
            
            # Количество задач
            cursor.execute('SELECT COUNT(*) as count FROM tasks')
            total_tasks = cursor.fetchone()['count']
            
            return {
                'status': 'success',
                'stats': {
                    'total_users': total_users,
                    'total_entries': total_entries,
                    'total_files': total_files,
                    'total_tasks': total_tasks,
                    'issues': 0  # Можно добавить проверку проблем
                }
            }
        except Exception as e:
            self.logger.exception("Ошибка при получении статистики")
            return {'status': 'error', 'message': f'Ошибка получения статистики: {str(e)}'}
        
    def download_file(self, request):
        """Скачивание файла"""
        try:
            file_id = int(request.get('file_id'))
        except (ValueError, TypeError):
            return {'status': 'error', 'message': 'Неверный идентификатор файла'}
        
        user_id = request.get('user_id')
        role = request.get('role')
        
        cursor = self.db.cursor()
        
        # Проверяем доступ к файлу
        if role == 'admin':
            cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        else:
            cursor.execute('SELECT * FROM files WHERE id = ? AND user_id = ?', (file_id, user_id))
        
        file = cursor.fetchone()
        
        if not file:
            return {'status': 'error', 'message': 'Файл не найден или доступ запрещен'}
        
        try:
            # Читаем файл с диска
            # sqlite3.Row использует индексацию, а не .get()
            filepath = Path(file['filepath'])
            if not filepath.exists():
                return {'status': 'error', 'message': 'Файл не найден на сервере'}
            
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            # Кодируем в base64 для передачи
            file_data_b64 = base64.b64encode(file_data).decode('utf-8')
            
            # Получаем file_type из sqlite3.Row (используем try/except для безопасности)
            try:
                file_type = file['file_type'] if file['file_type'] is not None else ''
            except (KeyError, IndexError):
                file_type = ''
            
            return {
                'status': 'success',
                'filename': file['filename'],
                'file_data': file_data_b64,
                'file_type': file_type
            }
        except Exception as e:
            self.logger.exception("Ошибка при скачивании файла")
            return {'status': 'error', 'message': f'Ошибка скачивания файла: {e}'}
    
    def send_chat_message(self, request):
        """Отправка сообщения в чат (с поддержкой topic_id)"""
        user_id = request.get('user_id')
        message = request.get('message', '').strip()
        topic_id = request.get('topic_id', 1)
        
        if not message:
            return {'status': 'error', 'message': 'Сообщение не может быть пустым'}
        
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT username, full_name FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                return {'status': 'error', 'message': 'Пользователь не найден'}
            try:
                cursor.execute('''
                    INSERT INTO chat_messages (user_id, username, full_name, message, topic_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, user['username'], user['full_name'], message, topic_id))
            except sqlite3.OperationalError:
                cursor.execute('''
                    INSERT INTO chat_messages (user_id, username, full_name, message)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, user['username'], user['full_name'], message))
            self.db.commit()
            return {'status': 'success', 'created_at': datetime.now().isoformat()}
        except Exception as e:
            self.logger.exception("Ошибка при отправке сообщения")
            return {'status': 'error', 'message': str(e)}
    
    def get_chat_messages(self, request):
        """Получение сообщений чата по теме"""
        limit = request.get('limit', 50)
        topic_id = request.get('topic_id', 1)
        try:
            cursor = self.db.cursor()
            try:
                cursor.execute('''
                    SELECT id, user_id, username, full_name, message, created_at, topic_id
                    FROM chat_messages WHERE COALESCE(topic_id, 1) = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (topic_id, limit))
            except sqlite3.OperationalError:
                cursor.execute('''
                    SELECT id, user_id, username, full_name, message, created_at
                    FROM chat_messages ORDER BY created_at ASC LIMIT ?
                ''', (limit,))
            messages = cursor.fetchall()
            result = [dict(m) for m in messages]
            return {'status': 'success', 'messages': result}
        except Exception as e:
            self.logger.exception("Ошибка при получении сообщений")
            return {'status': 'error', 'message': str(e)}
    
    def get_chat_topics(self, request):
        """Список тем чата"""
        if not request.get('user_id'):
            return {'status': 'error', 'message': 'Не авторизован'}
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT id, title, created_by, created_at FROM chat_topics ORDER BY id')
            rows = cursor.fetchall()
            topics = [dict(r) for r in rows]
            return {'status': 'success', 'topics': topics}
        except sqlite3.OperationalError:
            return {'status': 'success', 'topics': [{'id': 1, 'title': 'Общий', 'created_by': None, 'created_at': None}]}
    
    def create_chat_topic(self, request):
        """Создать тему чата"""
        user_id = request.get('user_id')
        title = (request.get('title') or '').strip()
        if not title or len(title) > 100:
            return {'status': 'error', 'message': 'Название темы 1–100 символов'}
        try:
            cursor = self.db.cursor()
            cursor.execute('INSERT INTO chat_topics (title, created_by) VALUES (?, ?)', (title, user_id))
            self.db.commit()
            return {'status': 'success', 'id': cursor.lastrowid, 'title': title}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def update_chat_topic(self, request):
        """Редактировать тему (автор или админ)"""
        user_id = request.get('user_id')
        role = request.get('role')
        topic_id = request.get('topic_id')
        title = (request.get('title') or '').strip()
        if not title or not topic_id:
            return {'status': 'error', 'message': 'Некорректные данные'}
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT created_by FROM chat_topics WHERE id = ?', (topic_id,))
            row = cursor.fetchone()
            if not row:
                return {'status': 'error', 'message': 'Тема не найдена'}
            if role != 'admin' and (row['created_by'] or 0) != user_id:
                return {'status': 'error', 'message': 'Нет прав'}
            cursor.execute('UPDATE chat_topics SET title = ? WHERE id = ?', (title, topic_id))
            self.db.commit()
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def edit_chat_message(self, request):
        """Редактировать своё сообщение"""
        user_id = request.get('user_id')
        msg_id = request.get('message_id')
        message = (request.get('message') or '').strip()
        if not message or not msg_id:
            return {'status': 'error', 'message': 'Некорректные данные'}
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT user_id FROM chat_messages WHERE id = ?', (msg_id,))
            row = cursor.fetchone()
            if not row:
                return {'status': 'error', 'message': 'Сообщение не найдено'}
            if int(row['user_id']) != int(user_id):
                return {'status': 'error', 'message': 'Можно редактировать только свои сообщения'}
            cursor.execute('UPDATE chat_messages SET message = ? WHERE id = ?', (message, msg_id))
            self.db.commit()
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def delete_chat_message(self, request):
        """Удалить сообщение (автор или админ)"""
        user_id = request.get('user_id')
        role = request.get('role')
        msg_id = request.get('message_id')
        if not msg_id:
            return {'status': 'error', 'message': 'Некорректные данные'}
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT user_id FROM chat_messages WHERE id = ?', (msg_id,))
            row = cursor.fetchone()
            if not row:
                return {'status': 'error', 'message': 'Сообщение не найдено'}
            if role != 'admin' and int(row['user_id']) != int(user_id):
                return {'status': 'error', 'message': 'Можно удалить только своё сообщение'}
            cursor.execute('DELETE FROM chat_messages WHERE id = ?', (msg_id,))
            self.db.commit()
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_colleagues(self, request):
        """Список коллег для постановки задачи (админ — все сотрудники, сотрудник — другие сотрудники)"""
        user_id = request.get('user_id')
        role = request.get('role')
        if not user_id:
            return {'status': 'error', 'message': 'Не авторизован'}
        cursor = self.db.cursor()
        if role == 'admin':
            cursor.execute('SELECT id, username, full_name FROM users WHERE role = ? ORDER BY full_name', ('employee',))
        else:
            cursor.execute('SELECT id, username, full_name FROM users WHERE role = ? AND id != ? ORDER BY full_name', ('employee', user_id))
        rows = cursor.fetchall()
        colleagues = [dict(r) for r in rows]
        return {'status': 'success', 'colleagues': colleagues}
    
    def get_colleague_tasks(self, request):
        """Задачи коллегам за месяц (админ — все, сотрудник — где автор или исполнитель)"""
        user_id = request.get('user_id')
        role = request.get('role')
        year = request.get('year')
        month = request.get('month')
        if not user_id or year is None or month is None:
            return {'status': 'error', 'message': 'Укажите год и месяц'}
        try:
            cursor = self.db.cursor()
            if role == 'admin':
                cursor.execute('''
                    SELECT ct.*, u1.full_name AS created_by_name, u2.full_name AS assignee_name
                    FROM colleague_tasks ct
                    LEFT JOIN users u1 ON ct.created_by = u1.id
                    LEFT JOIN users u2 ON ct.assignee_id = u2.id
                    WHERE ct.year = ? AND ct.month = ?
                    ORDER BY ct.day, ct.created_at
                ''', (year, month))
            else:
                cursor.execute('''
                    SELECT ct.*, u1.full_name AS created_by_name, u2.full_name AS assignee_name
                    FROM colleague_tasks ct
                    LEFT JOIN users u1 ON ct.created_by = u1.id
                    LEFT JOIN users u2 ON ct.assignee_id = u2.id
                    WHERE ct.year = ? AND ct.month = ? AND (ct.created_by = ? OR ct.assignee_id = ?)
                    ORDER BY ct.day, ct.created_at
                ''', (year, month, user_id, user_id))
            rows = cursor.fetchall()
            result = [dict(r) for r in rows]
            return {'status': 'success', 'colleague_tasks': result}
        except sqlite3.OperationalError:
            return {'status': 'success', 'colleague_tasks': []}
    
    def create_colleague_task(self, request):
        """Создать задачу коллеге"""
        user_id = request.get('user_id')
        role = request.get('role')
        assignee_id = request.get('assignee_id')
        year = request.get('year')
        month = request.get('month')
        day = request.get('day')
        title = (request.get('title') or '').strip()
        description = (request.get('description') or '').strip()
        color = (request.get('color') or '#3498db').strip()
        file_id = request.get('file_id')
        if not assignee_id or year is None or month is None or day is None or not title:
            return {'status': 'error', 'message': 'Укажите кому, дату и название задачи'}
        if role != 'admin':
            cursor = self.db.cursor()
            cursor.execute('SELECT id, role FROM users WHERE id = ?', (assignee_id,))
            u = cursor.fetchone()
            if not u or u['role'] != 'employee':
                return {'status': 'error', 'message': 'Можно назначить задачу только сотруднику'}
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO colleague_tasks (created_by, assignee_id, year, month, day, title, description, color, file_id, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (user_id, assignee_id, year, month, day, title, description, color, file_id or None))
            self.db.commit()
            return {'status': 'success', 'id': cursor.lastrowid}
        except Exception as e:
            self.logger.exception("Ошибка создания задачи коллеге")
            return {'status': 'error', 'message': str(e)}
    
    def complete_colleague_task(self, request):
        """Отметить задачу коллеге выполненной"""
        user_id = request.get('user_id')
        role = request.get('role')
        task_id = request.get('task_id')
        if not task_id:
            return {'status': 'error', 'message': 'Некорректные данные'}
        try:
            cursor = self.db.cursor()
            cursor.execute('SELECT assignee_id FROM colleague_tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if not row:
                return {'status': 'error', 'message': 'Задача не найдена'}
            if role != 'admin' and int(row['assignee_id']) != int(user_id):
                return {'status': 'error', 'message': 'Только исполнитель может отметить задачу выполненной'}
            cursor.execute('UPDATE colleague_tasks SET completed = 1, completed_at = ? WHERE id = ?', (datetime.now().isoformat(), task_id))
            self.db.commit()
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def log_audit(self, user_id, action, details, ip_address):
        """Логирование действий"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO audit_log (user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, details, ip_address))
        self.db.commit()
        
    def stop(self):
        """Остановка сервера"""
        if self.server:
            self.server.close()
        if self.db:
            self.db.close()
        self.logger.info("Сервер остановлен")

if __name__ == "__main__":
    server = ScheduleServer()
    server.start()