# -*- coding: utf-8 -*-
"""
web_chat.py — Чат API (полная версия)
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import os
import json
from web_config import logger, get_db_connection, UPLOADS_DIR

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/topics', methods=['GET'])
def get_chat_topics():
    """Получить темы чата"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('SELECT id, title FROM chat_topics ORDER BY id')
    topics = [dict(row) for row in cursor.fetchall()]
    
    logger.debug(f"Chat topics: {topics}")

    return jsonify({'status': 'success', 'topics': topics})


@chat_bp.route('/topics', methods=['POST'])
def create_chat_topic():
    """Создать тему чата"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    title = data.get('title', '').strip()

    if not title:
        return jsonify({'status': 'error', 'message': 'Title required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('''
        INSERT INTO chat_topics (title, created_by, created_at)
        VALUES (?, ?, ?)
    ''', (title, session['user_id'], datetime.now()))

    db.commit()
    topic_id = cursor.lastrowid

    logger.info(f"Chat topic created: id={topic_id}, title={title}")

    return jsonify({
        'status': 'success',
        'message': 'Тема создана',
        'topic_id': topic_id
    })


@chat_bp.route('/messages', methods=['GET'])
def get_chat_messages():
    """Получить сообщения чата"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    topic_id = int(request.args.get('topic_id', 1))
    limit = int(request.args.get('limit', 100))

    logger.debug(f"Get messages: topic_id={topic_id}, limit={limit}")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('''
        SELECT m.id, m.user_id, m.username, m.full_name, m.message, m.created_at,
               m.attachment_file_id, m.vk_conversation_id,
               f.filename, f.filepath, f.file_type, f.file_size,
               f.id as file_id
        FROM chat_messages m
        LEFT JOIN files f ON m.attachment_file_id = f.id
        WHERE m.topic_id = ?
        ORDER BY m.created_at DESC
        LIMIT ?
    ''', (topic_id, limit))

    messages = []
    for row in cursor.fetchall():
        msg = dict(row)
        msg['has_attachment'] = msg['attachment_file_id'] is not None

        # Добавляем conversation_message_id для группировки (VK)
        # vk_conversation_id -> conversation_message_id для JS
        if msg.get('vk_conversation_id'):
            msg['conversation_message_id'] = msg['vk_conversation_id']

        # Добавляем информацию о файле для нового чата
        if msg['file_id']:
            msg['file'] = {
                'id': msg['file_id'],
                'filename': msg['filename'],
                'filepath': msg['filepath'],
                'file_type': msg['file_type'],
                'file_size': msg['file_size']
            }

        messages.append(msg)

    # Реверсируем чтобы старые были в начале (ASC для отображения)
    messages.reverse()

    logger.debug(f"Found {len(messages)} messages")

    return jsonify({'status': 'success', 'messages': messages})


@chat_bp.route('/send', methods=['POST'])
def send_chat_message():
    """Отправить сообщение в чат"""
    logger.debug(f"=== CHAT: POST /send ===")
    
    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    logger.debug(f"Request data: {data}")
    
    message = data.get('message', '').strip()
    topic_id = int(data.get('topic_id', 1))
    attachment_file_id = data.get('attachment_file_id')

    # Разрешаем отправку только файла без текста
    if not message and not attachment_file_id:
        logger.warning("Message or attachment required")
        return jsonify({'status': 'error', 'message': 'Message or attachment required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('''
        INSERT INTO chat_messages
        (user_id, username, full_name, message, topic_id, attachment_file_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        session['username'],
        session.get('full_name', ''),
        message if message else '',
        topic_id,
        attachment_file_id,
        datetime.now()
    ))

    db.commit()
    msg_id = cursor.lastrowid

    logger.info(f"Chat message sent: id={msg_id}, user={session['username']}, topic_id={topic_id}")

    # Отправляем в Socket.IO
    try:
        from web_server import socketio
        socketio.emit('chat_message', {
            'id': msg_id,
            'user_id': session['user_id'],
            'username': session['username'],
            'full_name': session.get('full_name', ''),
            'message': message if message else '',
            'topic_id': topic_id,
            'attachment_file_id': attachment_file_id,
            'created_at': datetime.now().isoformat()
        })  # broadcast=True удалён (не поддерживается)
        logger.debug(f"Socket event emitted: chat_message")
    except Exception as e:
        logger.warning(f"Socket emit warning: {e}")

    # Синхронизация с VK (если тема = 1 "Общий" или 3 "VK")
    if topic_id in [1, 3] and (message or attachment_file_id):  # 1=Общий, 3=VK
        try:
            import vk_bot
            config = vk_bot.get_config()
            chat_peer_id = config.get('chat_peer_id')

            if chat_peer_id:
                # Формируем сообщение с именем пользователя
                vk_message = f"[{session.get('full_name', session['username'])}]"
                if message:
                    vk_message += f": {message}"
                else:
                    vk_message += " отправил(а) файл"

                # Отправляем текст + вложение если есть
                result = False
                if attachment_file_id:
                    # Получаем путь к файлу
                    db = get_db_connection()
                    cursor = db.cursor()
                    cursor.execute('SELECT filepath, filename FROM files WHERE id = ?', (attachment_file_id,))
                    file_row = cursor.fetchone()
                    if file_row:
                        filepath = file_row['filepath']
                        filename = file_row['filename']
                        
                        # Проверяем существует ли файл
                        import os
                        if not os.path.exists(filepath):
                            # Пробуем относительный путь
                            alt_filepath = os.path.join('static', 'uploads', filename)
                            if os.path.exists(alt_filepath):
                                filepath = alt_filepath
                                logger.info(f"VK sync: using alternative path {filepath}")
                            else:
                                logger.error(f"VK sync: file not found at {filepath} or {alt_filepath}")
                                result = vk_bot.send_message(peer_id=int(chat_peer_id), message=f"{vk_message} [Файл: {filename}]")
                        
                        if os.path.exists(filepath):
                            logger.info(f"VK sync: sending attachment {filepath}")

                            # Определяем тип файла
                            if filepath.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                # Отправляем фото + текст одним сообщением
                                result = vk_bot.upload_photo(filepath, peer_id=int(chat_peer_id), caption=vk_message)
                            else:
                                # Отправляем документ + текст одним сообщением
                                result = vk_bot.upload_document(filepath, peer_id=int(chat_peer_id), caption=vk_message)
                        else:
                            logger.error(f"VK sync: file still not found at {filepath}")
                            result = vk_bot.send_message(peer_id=int(chat_peer_id), message=f"{vk_message} [Файл не найден]")
                    else:
                        logger.error(f"VK sync: file record not found for id={attachment_file_id}")
                else:
                    # Только текст
                    result = vk_bot.send_message(peer_id=int(chat_peer_id), message=vk_message)

                if result:
                    logger.info(f"VK sync: message sent to peer_id={chat_peer_id}")
                else:
                    logger.warning(f"VK sync: failed to send")
        except Exception as e:
            logger.warning(f"VK sync warning: {e}")
            # Не прерываем работу, если VK недоступен

    return jsonify({
        'status': 'success',
        'message': 'Сообщение отправлено',
        'id': msg_id
    })


@chat_bp.route('/upload', methods=['POST'])
def upload_chat_file():
    """Загрузить файл в чат"""
    logger.debug(f"=== CHAT: POST /upload ===")
    
    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if 'file' not in request.files:
        logger.warning("No file in request")
        return jsonify({'status': 'error', 'message': 'No file'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("Empty filename")
        return jsonify({'status': 'error', 'message': 'Empty filename'}), 400

    # Сохраняем файл с уникальным именем
    import uuid
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(file.filename)
    safe_name = f"{timestamp}_{unique_id}_{name}{ext}"
    filepath = os.path.join(UPLOADS_DIR, safe_name)
    
    # Создаём директорию если не существует
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file.save(filepath)
    
    logger.debug(f"File saved: {filepath}")

    # Записываем в БД
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO files (filename, filepath, user_id, year, month, day, file_type, file_size, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (file.filename, filepath, session['user_id'],
          datetime.now().year, datetime.now().month, datetime.now().day,
          file.content_type, os.path.getsize(filepath), datetime.now()))

    db.commit()
    file_id = cursor.lastrowid
    
    logger.info(f"File uploaded: id={file_id}, filename={file.filename}")

    return jsonify({
        'status': 'success',
        'message': 'Файл загружен',
        'file_id': file_id,
        'filename': file.filename
    })


@chat_bp.route('/messages/<int:message_id>', methods=['PUT'])
def update_chat_message(message_id):
    """Редактировать сообщение чата"""
    logger.debug(f"=== CHAT: PUT /messages/{message_id} ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    message = data.get('message', '').strip()

    if not message:
        logger.warning("Message required")
        return jsonify({'status': 'error', 'message': 'Message required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем что сообщение существует и принадлежит пользователю (или админ)
    cursor.execute('SELECT * FROM chat_messages WHERE id = ?', (message_id,))
    msg = cursor.fetchone()

    if not msg:
        logger.warning(f"Message {message_id} not found")
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404

    msg = dict(msg)
    if msg['user_id'] != session['user_id'] and session.get('role') != 'admin':
        logger.warning(f"User {session['username']} not allowed to edit message {message_id}")
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    # Обновляем сообщение
    cursor.execute('''
        UPDATE chat_messages SET message = ? WHERE id = ?
    ''', (message, message_id))

    db.commit()

    logger.info(f"Chat message updated: id={message_id}")

    return jsonify({
        'status': 'success',
        'message': 'Сообщение обновлено'
    })


@chat_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_chat_message(message_id):
    """Удалить сообщение чата"""
    logger.debug(f"=== CHAT: DELETE /messages/{message_id} ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем что сообщение существует и принадлежит пользователю (или админ)
    cursor.execute('SELECT * FROM chat_messages WHERE id = ?', (message_id,))
    msg = cursor.fetchone()

    if not msg:
        logger.warning(f"Message {message_id} not found")
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404

    msg = dict(msg)
    if msg['user_id'] != session['user_id'] and session.get('role') != 'admin':
        logger.warning(f"User {session['username']} not allowed to delete message {message_id}")
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    # Удаляем сообщение
    cursor.execute('DELETE FROM chat_messages WHERE id = ?', (message_id,))
    db.commit()

    logger.info(f"Chat message deleted: id={message_id}")

    return jsonify({
        'status': 'success',
        'message': 'Сообщение удалено'
    })
