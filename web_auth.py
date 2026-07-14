# -*- coding: utf-8 -*-
"""
web_auth.py — Роуты аутентификации и VK верификации
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from datetime import datetime, date
import hashlib
import secrets
import os
import json
from web_config import logger, get_db_connection, audit_log, send_telegram_message, DATA_DIR
import vk_verification
import vk_bot

auth_bp = Blueprint('auth', __name__)


def init_temp_tokens():
    """Инициализировать хранилище временных токенов"""
    if not hasattr(auth_bp, 'temp_tokens'):
        auth_bp.temp_tokens = {}
    return auth_bp.temp_tokens


def store_temp_token(username, user_id, channel=None, telegram_code=None):
    """Сохранить временный токен для верификации"""
    temp_token = secrets.token_hex(16)
    tokens = init_temp_tokens()
    tokens[temp_token] = {
        'username': username,
        'user_id': user_id,
        'expires': datetime.now().timestamp() + 300,  # 5 min
        'channel': channel
    }
    if telegram_code:
        tokens[temp_token]['telegram_code'] = telegram_code
    return temp_token


def get_temp_token(temp_token):
    """Получить данные временного токена"""
    tokens = init_temp_tokens()
    return tokens.get(temp_token)


def delete_temp_token(temp_token):
    """Удалить временный токен"""
    tokens = init_temp_tokens()
    if temp_token in tokens:
        del tokens[temp_token]


def is_token_expired(token_data):
    """Проверить истёк ли токен"""
    return datetime.now().timestamp() > token_data['expires']


def send_telegram_code(username, user_id):
    """Отправить код верификации в Telegram"""
    temp_token = store_temp_token(username, user_id, channel='telegram')
    code = secrets.randbelow(9000) + 1000
    auth_bp.temp_tokens[temp_token]['telegram_code'] = code

    try:
        config_path = os.path.join(DATA_DIR, 'telegram_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        token = config.get('token')
        chat_ids = config.get('report_chat_ids', [])
        text = f"🔐 Код верификации: {code}\nДействителен 5 минут."
        sent, total = send_telegram_message(chat_ids, text, token)
        logger.info(f"Telegram code sent: {sent}/{total}")
        return temp_token, True
    except Exception as e:
        logger.exception(f"Telegram send error: {e}")
        return temp_token, False


def send_vk_code(username, user_id):
    """Отправить код верификации ВКонтакте"""
    result = vk_verification.request_verification_code(username)
    logger.info(f"VK verification result: {result}")

    if result.get('success'):
        temp_token = store_temp_token(username, user_id, channel='vk')
        return temp_token, True
    else:
        logger.warning(f"VK verification failed: {result}")
        return None, False


def login_user(user, remember=False):
    """Выполнить вход пользователя"""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']
    session.modified = True  # Явно сохраняем сессию
    audit_log(user['id'], 'login', 'Успешный вход')
    logger.info(f"Login successful: user_id={user['id']}, username={user['username']}")


def handle_admin_login(user, channel):
    """Обработать вход администратора с верификацией"""
    username = user['username']
    user_id = user['id']

    if channel == 'vk':
        # Send code via VK
        logger.info(f"VK verification requested for {username}")
        temp_token, success = send_vk_code(username, user_id)

        if success:
            return jsonify({
                'status': 'need_code',
                'temp_token': temp_token,
                'message': 'Код отправлен в ВКонтакте'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Не удалось отправить код ВКонтакте'
            }), 500

    elif channel == 'telegram':
        # Telegram verification
        temp_token, success = send_telegram_code(username, user_id)

        if success:
            return jsonify({
                'status': 'need_code',
                'temp_token': temp_token,
                'message': 'Код отправлен в Telegram'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Ошибка отправки кода в Telegram'
            }), 500

    else:
        # No channel specified - require verification
        return jsonify({
            'status': 'error',
            'message': 'Выберите способ отправки кода (Telegram или ВКонтакте)'
        }), 400


def authenticate_user(username, password, channel='telegram'):
    """Аутентификация пользователя"""
    if not username or not password:
        return None, 'Username and password required'

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        'SELECT id, username, password_hash, role, full_name FROM users WHERE username = ?',
        (username,)
    )
    user = cursor.fetchone()

    if not user:
        logger.warning(f"User not found: {username}")
        return None, 'Неверные учётные данные'

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user['password_hash'] != password_hash:
        logger.warning(f"Wrong password for {username}")
        return None, 'Неверные учётные данные'

    # Admin requires additional verification
    if user['role'] == 'admin':
        return user, 'admin_needs_verification'

    # Regular employee login
    login_user(user)
    return user, 'success'


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'GET':
        return render_template('login.html')

    # POST - JSON login
    if request.content_type and 'application/json' in request.content_type:
        data = request.json or {}
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')
        channel = data.get('channel', 'telegram')

        logger.info(f"POST /login: username={username}, channel={channel}")

        user, result = authenticate_user(username, password, channel)

        if result == 'success':
            return jsonify({
                'status': 'success',
                'redirect': '/dashboard'
            })

        if result == 'admin_needs_verification':
            return handle_admin_login(user, channel)

        # Failed login
        audit_log(None, 'failed_login', f'Неудачный вход для {username}')
        return jsonify({'status': 'error', 'message': 'Неверные учётные данные'}), 401

    return jsonify({'status': 'error', 'message': 'Invalid request'}), 400


@auth_bp.route('/login/verify-telegram', methods=['POST'])
def verify_telegram():
    """Verify Telegram code"""
    data = request.json or {}
    temp_token = data.get('temp_token')
    code = data.get('code', '').strip()

    logger.info(f"Telegram verification: temp_token={temp_token}, code={code}")

    token_data = get_temp_token(temp_token)
    if not token_data:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 400

    if is_token_expired(token_data):
        delete_temp_token(temp_token)
        return jsonify({'status': 'error', 'message': 'Token expired'}), 400

    stored_code = token_data.get('telegram_code')
    if str(stored_code) != code:
        return jsonify({'status': 'error', 'message': 'Wrong code'}), 400

    # Success - login user
    user_id = token_data['user_id']
    username = token_data['username']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, role, full_name FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        session.modified = True  # Явно сохраняем сессию
        audit_log(user['id'], 'login', 'Telegram verification successful')
        logger.info(f"Telegram login successful: user_id={user['id']}")
        delete_temp_token(temp_token)
        return jsonify({'status': 'success', 'redirect': '/dashboard'})

    return jsonify({'status': 'error', 'message': 'User not found'}), 404


@auth_bp.route('/login/verify-vk', methods=['POST'])
def verify_vk():
    """Verify VK code"""
    data = request.json or {}
    temp_token = data.get('temp_token')
    code = data.get('code', '').strip()

    logger.info(f"VK verification: temp_token={temp_token}, code={code}")

    token_data = get_temp_token(temp_token)
    if not token_data:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 400

    if is_token_expired(token_data):
        delete_temp_token(temp_token)
        return jsonify({'status': 'error', 'message': 'Token expired'}), 400

    username = token_data['username']

    # Verify code via vk_verification module
    result = vk_verification.verify_code(username, code)
    logger.info(f"VK verify result: {result}")

    if result.get('success'):
        # Success - login user
        user_id = token_data['user_id']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, role, full_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session.modified = True  # Явно сохраняем сессию
            audit_log(user['id'], 'login', 'VK verification successful')
            logger.info(f"VK login successful: user_id={user['id']}")
            delete_temp_token(temp_token)
            return jsonify({'status': 'success', 'redirect': '/dashboard'})

    delete_temp_token(temp_token)
    return jsonify({'status': 'error', 'message': result.get('message', 'Verification failed')}), 400


@auth_bp.route('/logout')
def logout():
    """Logout"""
    user_id = session.get('user_id')
    if user_id:
        audit_log(user_id, 'logout', 'User logged out')
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('auth.login'))


# VK API routes
@auth_bp.route('/api/vk/send-code', methods=['POST'])
def api_vk_send_code():
    """Request verification code via VK"""
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    
    logger.info(f"VK VERIFY: Request for username='{username}'")
    
    if not username:
        logger.warning("VK VERIFY: Username empty")
        return jsonify({'status': 'error', 'error': 'Username required'}), 400
    
    result = vk_verification.request_verification_code(username)
    logger.info(f"VK VERIFY: Result={result}")
    
    if result.get('success'):
        logger.info(f"VK VERIFY: Success for {username}")
        return jsonify({'status': 'ok', 'message': 'Code sent via VK'})
    else:
        logger.warning(f"VK VERIFY: Error - {result.get('message')}")
        return jsonify({'status': 'error', 'error': result.get('message', 'Error')}), 500


@auth_bp.route('/api/vk/verify-code', methods=['POST'])
def api_vk_verify_code():
    """Verify VK code"""
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    code = data.get('code', '').strip()
    
    logger.info(f"VK VERIFY: username={username}, code={code}")
    
    if not username or not code:
        return jsonify({'status': 'error', 'error': 'Username and code required'}), 400
    
    result = vk_verification.verify_code(username, code)
    logger.info(f"VK VERIFY: Result={result}")
    
    if result.get('success'):
        return jsonify({'status': 'ok', 'message': 'Verification successful'})
    else:
        return jsonify({'status': 'error', 'error': result.get('message', 'Verification failed')}), 400
