# -*- coding: utf-8 -*-
"""
web_chat.py — Чат с интеграцией ВКонтакте

Функции:
- Отправка сообщений в чат группы VK
- Получение сообщений от сотрудников
- Загрузка файлов/фото
- Socket.IO уведомления
"""
from flask import Blueprint, request, jsonify, session
from flask_socketio import emit
from datetime import datetime
import os
import json
import shutil
from web_config import logger, get_db_connection, DATA_DIR, UPLOADS_DIR
import vk_bot

chat_bp = Blueprint('chat', __name__)

# Папка для загрузок из VK
VK_UPLOADS_DIR = os.path.join(UPLOADS_DIR, 'vk')
os.makedirs(VK_UPLOADS_DIR, exist_ok=True)


# ==========================================
# API Роуты
# ==========================================

@chat_bp.route('/messages')
def get_chat_messages():
    """Получить сообщения чата"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    topic_id = request.args.get('topic_id', 1)
    limit = request.args.get('limit', 50)

    db = get_db_connection()
    cursor = db.cursor()

    # Получаем сообщения из БД (chat_messages)
    cursor.execute('''
        SELECT m.id, m.user_id, m.username, m.full_name, m.message, m.created_at
        FROM chat_messages m
        WHERE m.topic_id = ?
        ORDER BY m.created_at DESC
        LIMIT ?
    ''', (topic_id, limit))

    messages = []
    for row in cursor.fetchall():
        messages.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'username': row['username'],
            'full_name': row['full_name'],
            'message': row['message'],
            'created_at': row['created_at']
        })
            'message_text': row['message_text'],
            'has_attachment': row['has_attachment'],
            'attachment_type': row['attachment_type'],
            'attachment_path': row['attachment_path'],
            'direction': row['direction'],
            'created_at': row['created_at'],
            'full_name': row['full_name'] or f'VK-{row["vk_id"]}',
            'username': row['username']
        })
    
    # Переворачиваем (новые внизу)
    messages.reverse()
    
    return jsonify({'status': 'success', 'messages': messages})


@chat_bp.route('/send', methods=['POST'])
def send_chat_message():
    """Отправить сообщение в чат"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}
    text = data.get('text', '').strip()
    topic_id = int(data.get('topic_id', 1))

    if not text:
        return jsonify({'status': 'error', 'message': 'Message is empty'}), 400
    
    # Получаем конфигурацию VK
    config = vk_bot.get_config()
    chat_peer_id = config.get('chat_peer_id')
    
    if not chat_peer_id:
        return jsonify({
            'status': 'error',
            'message': 'VK chat not configured. Set chat_peer_id in vk_config.json'
        }), 500
    
    # Отправляем в VK
    try:
        result = vk_bot.send_message(peer_id=int(chat_peer_id), message=text)
        
        if result:
            # Сохраняем в БД
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO vk_messages 
                (vk_id, user_id, message_text, direction, topic_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (0, session['user_id'], text, 'outgoing', topic_id, datetime.now()))
            
            message_id = cursor.lastrowid
            db.commit()
            
            # Уведомляем через Socket.IO
            emit('chat_message', {
                'id': message_id,
                'user_id': session['user_id'],
                'full_name': session.get('full_name'),
                'message_text': text,
                'direction': 'outgoing',
                'created_at': datetime.now().isoformat()
            }, broadcast=True)
            
            logger.info(f"Chat message sent to VK chat: {text[:50]}...")
            return jsonify({'status': 'success', 'message_id': message_id})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send to VK'}), 500
            
    except Exception as e:
        logger.exception(f"Chat send error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@chat_bp.route('/upload', methods=['POST'])
def upload_chat_file():
    """Загрузить файл в чат"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Empty filename'}), 400
    
    # Создаём папку по месяцам
    date_folder = datetime.now().strftime('%Y-%m')
    month_dir = os.path.join(VK_UPLOADS_DIR, date_folder)
    os.makedirs(month_dir, exist_ok=True)
    
    # Сохраняем файл
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in '._- ')
    file_path = os.path.join(month_dir, safe_name)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    
    # Отправляем в VK
    config = vk_bot.get_config()
    chat_peer_id = config.get('chat_peer_id')
    
    if not chat_peer_id:
        return jsonify({'status': 'error', 'message': 'VK chat not configured'}), 500
    
    try:
        # Определяем тип файла
        ext = os.path.splitext(file.filename)[1].lower()
        is_photo = ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        if is_photo:
            # Загружаем как фото
            result = vk_bot.upload_photo(file_path, int(chat_peer_id))
            attachment_type = 'photo'
        else:
            # Загружаем как документ
            result = vk_bot.upload_document(file_path, int(chat_peer_id))
            attachment_type = 'document'
        
        if result:
            # Сохраняем в БД
            db = get_db_connection()
            cursor = db.cursor()
            
            cursor.execute('''
                INSERT INTO vk_messages 
                (vk_id, user_id, message_text, has_attachment, attachment_type, 
                 attachment_path, direction, topic_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (0, session['user_id'], safe_name, 1, attachment_type, 
                  file_path, 'outgoing', 1, datetime.now()))
            
            message_id = cursor.lastrowid
            
            # Сохраняем вложение
            cursor.execute('''
                INSERT INTO vk_attachments 
                (message_id, file_type, file_path, file_size, original_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, attachment_type, file_path, file_size, file.filename, datetime.now()))
            
            db.commit()
            
            # Уведомляем через Socket.IO
            emit('chat_message', {
                'id': message_id,
                'user_id': session['user_id'],
                'full_name': session.get('full_name'),
                'message_text': safe_name,
                'has_attachment': 1,
                'attachment_type': attachment_type,
                'attachment_path': file_path,
                'direction': 'outgoing',
                'created_at': datetime.now().isoformat()
            }, broadcast=True)
            
            logger.info(f"Chat file uploaded: {file.filename} ({attachment_type})")
            return jsonify({
                'status': 'success',
                'message_id': message_id,
                'file_path': file_path
            })
        else:
            return jsonify({'status': 'error', 'message': 'Failed to upload to VK'}), 500
            
    except Exception as e:
        logger.exception(f"Chat upload error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@chat_bp.route('/attachments/<int:message_id>')
def get_message_attachments(message_id):
    """Получить вложения сообщения"""
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT file_type, file_path, file_size, original_name
        FROM vk_attachments
        WHERE message_id = ?
    ''', (message_id,))
    
    attachments = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'status': 'success', 'attachments': attachments})


@chat_bp.route('/vk-status')
def get_vk_chat_status():
    """Получить статус подключения VK чата"""
    config = vk_bot.get_config()
    
    status = {
        'vk_token': 'configured' if config.get('service_token') else 'not_configured',
        'group_id': config.get('group_id'),
        'chat_peer_id': config.get('chat_peer_id'),
        'admin_vk_id': config.get('admin_vk_id'),
        'vk_user_map': config.get('vk_user_map', {}),
        'status': 'ok' if config.get('service_token') and config.get('chat_peer_id') else 'error'
    }
    
    return jsonify(status)


# ==========================================
# Socket.IO Обработчики
# ==========================================

def on_chat_connect():
    """Клиент подключился к чату"""
    logger.info(f"Client connected to chat: {request.sid if request else 'unknown'}")
    emit('chat_connected', {'status': 'ok'})


def on_chat_disconnect():
    """Клиент отключился от чата"""
    logger.info(f"Client disconnected from chat: {request.sid if request else 'unknown'}")


# ==========================================
# Обработка входящих сообщений из VK
# ==========================================

def process_vk_message_event(event_data):
    """
    Обработать входящее сообщение из VK
    
    Вызывается из vk_bot.py при получении message_new
    """
    message = event_data.get('message', {})
    from_id = abs(message.get('from_id', 0))
    peer_id = message.get('peer_id')
    text = message.get('text', '')
    attachments = message.get('attachments', [])
    
    if from_id <= 0:  # Игнорируем сообщения от ботов
        return
    
    logger.info(f"VK chat message from {from_id}: {text[:50]}...")
    
    # Находим user_id по VK ID
    config = vk_bot.get_config()
    user_map = config.get('vk_user_map', {})
    user_id = None
    
    for vk_uid, uid in user_map.items():
        if int(vk_uid) == from_id:
            user_id = uid
            break
    
    # Сохраняем в БД
    db = get_db_connection()
    cursor = db.cursor()
    
    has_attachment = 1 if attachments else 0
    attachment_type = attachments[0].get('type') if attachments else None
    attachment_path = None
    
    # Сохраняем вложения если есть
    if attachments:
        for att in attachments:
            att_type = att.get('type')
            att_data = att.get(att_type, {})
            
            if att_type == 'photo':
                # Сохраняем URL фото
                photo_url = att_data.get('sizes', [{}])[-1].get('url')
                if photo_url:
                    # Скачиваем фото
                    import urllib.request
                    date_folder = datetime.now().strftime('%Y-%m')
                    month_dir = os.path.join(VK_UPLOADS_DIR, date_folder)
                    os.makedirs(month_dir, exist_ok=True)
                    
                    file_name = f"photo_{from_id}_{att_data.get('id')}.jpg"
                    file_path = os.path.join(month_dir, file_name)
                    
                    try:
                        urllib.request.urlretrieve(photo_url, file_path)
                        attachment_path = file_path
                    except Exception as e:
                        logger.warning(f"Failed to download photo: {e}")
                        attachment_path = photo_url
            
            elif att_type == 'doc':
                # Сохраняем документ
                doc_url = att_data.get('url')
                if doc_url:
                    import urllib.request
                    date_folder = datetime.now().strftime('%Y-%m')
                    month_dir = os.path.join(VK_UPLOADS_DIR, date_folder)
                    os.makedirs(month_dir, exist_ok=True)
                    
                    file_name = att_data.get('title', f'doc_{att_data.get("id")}')
                    file_path = os.path.join(month_dir, file_name)
                    
                    try:
                        urllib.request.urlretrieve(doc_url, file_path)
                        attachment_path = file_path
                    except Exception as e:
                        logger.warning(f"Failed to download doc: {e}")
                        attachment_path = doc_url
    
    # Вставляем сообщение
    cursor.execute('''
        INSERT INTO vk_messages 
        (vk_id, user_id, message_text, has_attachment, attachment_type, 
         attachment_path, direction, topic_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (from_id, user_id, text, has_attachment, attachment_type, 
          attachment_path, 'incoming', 1, datetime.now()))
    
    message_id = cursor.lastrowid
    
    # Сохраняем вложение в отдельную таблицу
    if attachment_path:
        cursor.execute('''
            INSERT INTO vk_attachments 
            (message_id, file_type, file_path, file_size, original_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, attachment_type, attachment_path, 0, text, datetime.now()))
    
    db.commit()
    
    # Уведомляем через Socket.IO
    emit('chat_message', {
        'id': message_id,
        'vk_id': from_id,
        'user_id': user_id,
        'full_name': f'VK-{from_id}',
        'message_text': text,
        'has_attachment': has_attachment,
        'attachment_type': attachment_type,
        'attachment_path': attachment_path,
        'direction': 'incoming',
        'created_at': datetime.now().isoformat()
    }, broadcast=True, namespace='/chat')
    
    logger.info(f"VK chat message saved: id={message_id}")
