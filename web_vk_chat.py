# -*- coding: utf-8 -*-
"""
web_vk_chat.py — Полная интеграция чата с ВКонтакте

Функции:
- Синхронизация сообщений между веб-чатом и VK группой
- Загрузка файлов из VK на сервер
- Отправка сообщений в VK от имени пользователя
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import os
import json
import urllib.request
import ssl
import sqlite3
import time
import random
from web_config import logger, get_db_connection, DATA_DIR, UPLOADS_DIR
import vk_bot

# SSL-контекст без проверки сертификата (для VK API)
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

vk_chat_bp = Blueprint('vk_chat', __name__)

# ID темы для VK чата
# VK сообщения идут в отдельную тему "VK" (topic_id=3)
VK_PERMANENT_TOPIC_ID = 3


@vk_chat_bp.route('/vk-sync', methods=['POST'])
def sync_vk_messages():
    """
    Получить новые сообщения из VK и сохранить в БД
    Вызывается из vk_bot.py при получении message_new
    
    Логика:
    - Если есть текст + вложения: создаём одно сообщение с первым вложением
    - Если несколько вложений без текста: создаём отдельное сообщение для каждого
    - Если только текст: одно сообщение
    - Защита от дубликатов по conversation_message_id
    - Получение вложений из 4 источников (Long Poll + API)
    """
    try:
        data = request.json or {}
        event = data.get('event', {})
        message = event.get('message', {})
        
        # Получаем вложения ИЗ ДАННЫХ VK БОТА (он уже получил через API)
        # Приоритет: attachments из data > event > object.message > message
        attachments = data.get('attachments', [])  # VK бот уже получил через API
        
        if not attachments:
            attachments = message.get('attachments', [])
        if not attachments:
            attachments = event.get('attachments', [])
        if not attachments:
            object_data = event.get('object', {})
            obj_message = object_data.get('message', {})
            attachments = obj_message.get('attachments', [])

        from_id = abs(message.get('from_id', 0))
        peer_id = message.get('peer_id')
        text = message.get('text', '')
        conversation_message_id = message.get('conversation_message_id')
        
        # УНИКАЛЬНЫЙ ID для проверки дубликатов
        unique_key = f"{from_id}_{conversation_message_id}"
        
        # Логируем для отладки
        logger.info(f"VK sync received: from_id={from_id}, cid={conversation_message_id}, text='{text[:30]}...', attachments={len(attachments)}")
        logger.info(f"VK unique_key: {unique_key}")
        logger.info(f"VK event keys: {list(event.keys())}")
        logger.info(f"VK message keys: {list(message.keys())}")
        
        # Если вложений много, логируем подробно
        if len(attachments) > 1:
            logger.info(f"VK MULTIPLE ATTACHMENTS DETECTED: {len(attachments)} files")
            for i, att in enumerate(attachments):
                att_type = att.get('type', 'unknown')
                logger.info(f"  Attachment {i+1}: type={att_type}")
        
        # Логируем первое вложение для отладки
        if attachments:
            logger.info(f"VK First attachment: {attachments[0]}")

        if from_id <= 0:
            logger.warning(f"Invalid from_id: {from_id}")
            return jsonify({'status': 'ignored'})

        # Проверяем что это из чата группы (peer_id >= 2000000000)
        if peer_id is None or peer_id < 2000000000:
            logger.warning(f"Invalid peer_id: {peer_id}")
            return jsonify({'status': 'ignored', 'reason': 'not group chat'})

        # ПРОВЕРКА НА ДУБЛИКАТЫ
        # Создаём временную таблицу для отслеживания обработанных сообщений
        db = get_db_connection()
        cursor = db.cursor()
        
        # Проверяем, не обрабатывали ли уже это сообщение
        cursor.execute('''
            SELECT id FROM chat_messages 
            WHERE vk_conversation_id = ? 
            LIMIT 1
        ''', (unique_key,))
        
        existing = cursor.fetchone()
        if existing:
            logger.info(f"VK DUPLICATE DETECTED: {unique_key} - message already processed (id={existing[0]})")
            return jsonify({'status': 'duplicate', 'message_id': existing[0]})
        
        # Продолжаем обработку если не дубликат

        # Получаем конфиг и user_map
        config = vk_bot.get_config()
        user_map = config.get('vk_user_map', {})
        user_id = None
        full_name = f'VK-{from_id}'

        # Находим user_id по VK ID
        for vk_uid, uid in user_map.items():
            if int(vk_uid) == from_id:
                user_id = uid
                # Получаем имя из БД
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute('SELECT full_name FROM users WHERE id = ?', (uid,))
                row = cursor.fetchone()
                if row:
                    full_name = row['full_name']
                break

        # Если user_id не найден, создаём временного пользователя
        if user_id is None:
            logger.info(f"VK user {from_id} not mapped - will use guest mode")
            full_name = f'VK User {from_id}'
            # Получаем информацию о пользователе из VK API
            try:
                vk_info = vk_bot.get_user_info(from_id)
                if vk_info:
                    first_name = vk_info.get('first_name', '')
                    last_name = vk_info.get('last_name', '')
                    full_name = f'{first_name} {last_name}'.strip() or f'VK-{from_id}'
            except Exception as e:
                logger.warning(f"Could not get VK user info: {e}")

        logger.info(f"VK user mapping: vk_id={from_id} -> user_id={user_id}, full_name={full_name}")

        db = get_db_connection()
        cursor = db.cursor()

        # Обрабатываем все вложения и сохраняем file_id
        attachment_ids = []
        
        if attachments:
            logger.info(f"VK attachments: {len(attachments)}")
            for idx, att in enumerate(attachments):
                att_type = att.get('type')
                filepath = None
                filename = None
                file_type = None

                try:
                    if att_type == 'photo':
                        photo = att.get('photo')
                        # Берём URL из sizes массива (наибольшее качество)
                        photo_url = None
                        sizes = photo.get('sizes', [])
                        if sizes:
                            # Сортируем по высоте и берём наибольшее
                            sizes_sorted = sorted(sizes, key=lambda x: x.get('height', 0), reverse=True)
                            photo_url = sizes_sorted[0].get('url')
                        
                        # Если не нашли в sizes, пробуем старые поля
                        if not photo_url:
                            photo_url = (photo.get('photo_256') or photo.get('photo_128') or 
                                        photo.get('photo_807') or photo.get('photo_604'))

                        if photo_url:
                            # Уникальное имя с timestamp и random
                            suffix = f"_{idx}_{random.randint(1000,9999)}" if len(attachments) > 1 else f"_{random.randint(1000,9999)}"
                            filename = f"vk_photo_{from_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}.jpg"
                            filepath = os.path.join(UPLOADS_DIR, filename)

                            # Скачиваем фото с SSL-контекстом (игнорируем проверку сертификата)
                            req = urllib.request.Request(photo_url)
                            with urllib.request.urlopen(req, context=_ssl_context, timeout=30) as response:
                                with open(filepath, 'wb') as f:
                                    f.write(response.read())
                            file_type = 'image/jpeg'
                            logger.info(f"VK photo downloaded: {filename}, size={os.path.getsize(filepath)}")
                        else:
                            logger.warning(f"VK photo has no URL: {att}")

                    elif att_type == 'doc':
                        doc = att.get('doc')
                        doc_url = doc.get('url')
                        orig_filename = doc.get('title', 'document')

                        if doc_url:
                            ext = os.path.splitext(orig_filename)[1] or '.dat'
                            # Уникальное имя с timestamp и random
                            suffix = f"_{idx}_{random.randint(1000,9999)}" if len(attachments) > 1 else f"_{random.randint(1000,9999)}"
                            filename = f"vk_doc_{from_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}{ext}"
                            filepath = os.path.join(UPLOADS_DIR, filename)

                            # Скачиваем документ с SSL-контекстом (игнорируем проверку сертификата)
                            req = urllib.request.Request(doc_url)
                            with urllib.request.urlopen(req, context=_ssl_context, timeout=30) as response:
                                with open(filepath, 'wb') as f:
                                    f.write(response.read())
                            file_type = doc.get('type', 'application/octet-stream')
                            logger.info(f"VK document downloaded: {filename}, size={os.path.getsize(filepath)}")
                        else:
                            logger.warning(f"VK document has no URL: {att}")

                    # Audio и Video не поддерживаются VK Bot API - пропускаем
                    elif att_type == 'audio':
                        logger.warning(f"VK audio not supported: {att.get('audio', {}).get('title', 'unknown')}")
                    elif att_type == 'video':
                        logger.warning(f"VK video not supported: {att.get('video', {}).get('title', 'unknown')}")

                    # Сохраняем в БД файлов если файл скачан
                    if filepath and os.path.exists(filepath):
                        # Пробуем несколько раз при блокировке БД
                        max_retries = 3
                        for retry in range(max_retries):
                            try:
                                cursor.execute('''
                                    INSERT INTO files (filename, filepath, file_type, user_id, year, month, day, file_type, file_size, uploaded_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (filename, filepath, file_type, user_id,
                                      datetime.now().year, datetime.now().month, datetime.now().day,
                                      file_type, os.path.getsize(filepath), datetime.now()))
                                db.commit()
                                file_id = cursor.lastrowid
                                attachment_ids.append(file_id)
                                logger.info(f"VK attachment saved to files: id={file_id}, path={filepath}")
                                break
                            except sqlite3.OperationalError as e:
                                if 'locked' in str(e) and retry < max_retries - 1:
                                    logger.warning(f"DB locked, retry {retry+1}/{max_retries}...")
                                    time.sleep(0.5)
                                    db.rollback()
                                else:
                                    logger.error(f"DB error: {e}")
                                    raise
                    else:
                        logger.warning(f"VK attachment file not found: {filepath}")

                except Exception as e:
                    logger.error(f"Error processing attachment: {e}", exc_info=True)

        logger.info(f"VK sync: processed {len(attachment_ids)} attachments, text='{text[:30]}...'")

        # Создаём сообщения в БД
        created_messages = []

        if text and attachment_ids:
            # Есть текст + вложения: создаём одно сообщение с первым вложением
            cursor.execute('''
                INSERT INTO chat_messages
                (user_id, username, full_name, message, topic_id, attachment_file_id, created_at, vk_conversation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                f'vk_user_{from_id}',
                full_name,
                text,
                VK_PERMANENT_TOPIC_ID,
                attachment_ids[0],  # Первое вложение
                datetime.now(),
                unique_key  # Уникальный ID для защиты от дубликатов
            ))
            db.commit()
            msg_id = cursor.lastrowid
            created_messages.append(msg_id)
            logger.info(f"VK message synced: vk_id={from_id}, user_id={user_id}, msg_id={msg_id}, attachment={attachment_ids[0]}, vk_cid={unique_key}")

            # Если вложений больше 1, создаём дополнительные сообщения без текста
            for extra_file_id in attachment_ids[1:]:
                cursor.execute('''
                    INSERT INTO chat_messages
                    (user_id, username, full_name, message, topic_id, attachment_file_id, created_at, vk_conversation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    f'vk_user_{from_id}',
                    full_name,
                    '',  # Без текста
                    VK_PERMANENT_TOPIC_ID,
                    extra_file_id,
                    datetime.now(),
                    unique_key  # Тот же уникальный ID
                ))
                db.commit()
                extra_msg_id = cursor.lastrowid
                created_messages.append(extra_msg_id)
                logger.info(f"VK extra attachment: msg_id={extra_msg_id}, attachment={extra_file_id}, vk_cid={unique_key}")

        elif text:
            # Только текст
            cursor.execute('''
                INSERT INTO chat_messages
                (user_id, username, full_name, message, topic_id, attachment_file_id, created_at, vk_conversation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                f'vk_user_{from_id}',
                full_name,
                text,
                VK_PERMANENT_TOPIC_ID,
                None,
                datetime.now(),
                unique_key
            ))
            db.commit()
            msg_id = cursor.lastrowid
            created_messages.append(msg_id)
            logger.info(f"VK text message synced: vk_id={from_id}, user_id={user_id}, msg_id={msg_id}, vk_cid={unique_key}")

        elif attachment_ids:
            # Только вложения без текста: создаём сообщение для каждого
            for file_id in attachment_ids:
                cursor.execute('''
                    INSERT INTO chat_messages
                    (user_id, username, full_name, message, topic_id, attachment_file_id, created_at, vk_conversation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    f'vk_user_{from_id}',
                    full_name,
                    '',  # Без текста
                    VK_PERMANENT_TOPIC_ID,
                    file_id,
                    datetime.now(),
                    unique_key
                ))
                db.commit()
                msg_id = cursor.lastrowid
                created_messages.append(msg_id)
                logger.info(f"VK attachment message: vk_id={from_id}, msg_id={msg_id}, attachment={file_id}, vk_cid={unique_key}")
        else:
            logger.warning(f"VK sync: no text and no attachments - empty message ignored")

        # Отправляем Socket.IO события для новых сообщений
        if created_messages:
            try:
                from web_server import socketio
                for msg_id in created_messages:
                    cursor.execute('''
                        SELECT m.id, m.user_id, m.username, m.full_name, m.message, m.created_at, m.attachment_file_id,
                               f.filename, f.filepath
                        FROM chat_messages m
                        LEFT JOIN files f ON m.attachment_file_id = f.id
                        WHERE m.id = ?
                    ''', (msg_id,))
                    row = cursor.fetchone()
                    if row:
                        msg = dict(row)
                        # Исправляем ошибку isoformat: created_at может быть уже строкой
                        created_at = msg['created_at']
                        if isinstance(created_at, datetime):
                            created_at_str = created_at.isoformat()
                        elif isinstance(created_at, str):
                            created_at_str = created_at
                        else:
                            created_at_str = datetime.now().isoformat()
                        
                        socketio.emit('chat_message', {
                            'id': msg['id'],
                            'user_id': msg['user_id'] or 0,
                            'username': msg['username'],
                            'full_name': msg['full_name'],
                            'message': msg['message'] or '',
                            'topic_id': VK_PERMANENT_TOPIC_ID,
                            'attachment_file_id': msg['attachment_file_id'],
                            'created_at': created_at_str
                        })
                logger.info(f"Socket.IO: отправлено {len(created_messages)} сообщений")
            except Exception as e:
                logger.warning(f"Socket emit warning: {e}")

        return jsonify({
            'status': 'success',
            'message_ids': created_messages
        })

    except Exception as e:
        logger.exception(f"VK sync error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@vk_chat_bp.route('/vk/send', methods=['POST'])
def send_to_vk():
    """
    Отправить сообщение из веб-чата в VK группу
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}
    message = data.get('message', '').strip()
    topic_id = int(data.get('topic_id', 1))
    
    if not message:
        return jsonify({'status': 'error', 'message': 'Message required'}), 400
    
    config = vk_bot.get_config()
    chat_peer_id = config.get('chat_peer_id')
    
    if not chat_peer_id:
        return jsonify({'status': 'error', 'message': 'VK chat not configured'}), 500
    
    # Формируем сообщение с именем пользователя
    vk_message = f"[{session.get('full_name', session['username'])}]: {message}"
    
    try:
        result = vk_bot.send_message(peer_id=int(chat_peer_id), message=vk_message)
        
        if result:
            logger.info(f"Message sent to VK: {message[:50]}...")
            return jsonify({'status': 'success', 'message': 'Отправлено в VK'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send to VK'}), 500
            
    except Exception as e:
        logger.exception(f"VK send error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@vk_chat_bp.route('/vk/create-topic', methods=['POST'])
def create_vk_topic():
    """
    Создать новую тему в чате VK группы
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}
    title = data.get('title', '').strip()
    
    if not title:
        return jsonify({'status': 'error', 'message': 'Title required'}), 400
    
    config = vk_bot.get_config()
    group_id = config.get('group_id')
    
    if not group_id:
        return jsonify({'status': 'error', 'message': 'Group ID not configured'}), 500
    
    # Создаём тему через VK API
    try:
        # VK API для создания тем: board.createTopic
        result = vk_bot._api_request('board.createTopic', {
            'group_id': group_id,
            'title': title
        })
        
        if result and result.get('topic_id'):
            topic_id = result['topic_id']
            logger.info(f"VK topic created: id={topic_id}, title={title}")
            
            # Сохраняем в БД
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO chat_topics (title, created_by, created_at)
                VALUES (?, ?, ?)
            ''', (title, session['user_id'], datetime.now()))
            db.commit()
            
            return jsonify({
                'status': 'success',
                'topic_id': topic_id,
                'message': f'Тема "{title}" создана в VK'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Failed to create topic in VK'}), 500
            
    except Exception as e:
        logger.exception(f"VK create topic error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@vk_chat_bp.route('/vk/download-attachment', methods=['POST'])
def download_vk_attachment():
    """
    Скачать вложение из VK на сервер
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}
    attachment_url = data.get('url')
    attachment_type = data.get('type', 'document')
    
    if not attachment_url:
        return jsonify({'status': 'error', 'message': 'URL required'}), 400
    
    try:
        # Создаём папку для загрузок из VK
        date_folder = datetime.now().strftime('%Y-%m')
        vk_dir = os.path.join(UPLOADS_DIR, 'vk', date_folder)
        os.makedirs(vk_dir, exist_ok=True)
        
        # Генерируем имя файла
        filename = f"vk_{attachment_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if attachment_type == 'photo':
            filename += '.jpg'
        else:
            filename += '.dat'
        
        filepath = os.path.join(vk_dir, filename)
        
        # Скачиваем файл
        urllib.request.urlretrieve(attachment_url, filepath)
        
        file_size = os.path.getsize(filepath)
        
        logger.info(f"VK attachment downloaded: {filepath} ({file_size} bytes)")
        
        return jsonify({
            'status': 'success',
            'filepath': filepath,
            'filename': filename,
            'size': file_size
        })
        
    except Exception as e:
        logger.exception(f"VK download error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@vk_chat_bp.route('/vk/status')
def vk_chat_status():
    """
    Проверить статус интеграции с VK
    """
    config = vk_bot.get_config()

    status = {
        'vk_token': 'configured' if config.get('service_token') else 'not_configured',
        'group_id': config.get('group_id'),
        'chat_peer_id': config.get('chat_peer_id'),
        'vk_user_map': config.get('vk_user_map', {}),
        'status': 'ok' if config.get('service_token') and config.get('chat_peer_id') else 'error'
    }

    return jsonify(status)


@vk_chat_bp.route('/vk-seen-users', methods=['GET'])
def api_get_vk_seen_users():
    """Получить участников VK и привязку к пользователям"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403

    import json
    from web_config import get_db_connection

    db = get_db_connection()
    cursor = db.cursor()

    # Читаем VK конфиг
    vk_config_path = os.path.join(DATA_DIR, 'vk_config.json')
    try:
        with open(vk_config_path, 'r', encoding='utf-8') as f:
            vk_config = json.load(f)
    except:
        return jsonify({'status': 'error', 'message': 'VK конфиг не найден'}), 404

    # Получаем привязку vk_user_map из конфига
    vk_user_map = vk_config.get('vk_user_map', {})  # {vk_id: user_id}

    # Получаем всех пользователей
    cursor.execute('SELECT id, username, full_name FROM users ORDER BY full_name')
    users = [{'id': r['id'], 'username': r['username'], 'full_name': r['full_name']} for r in cursor.fetchall()]

    # Создаём обратную карту: user_id -> vk_id
    user_vk_map = {}
    for vk_id_str, user_id_str in vk_user_map.items():
        user_vk_map[user_id_str] = vk_id_str

    # Формируем список: каждый пользователь с его VK
    seen = []
    for user in users:
        user_id_str = str(user['id'])
        vk_id = user_vk_map.get(user_id_str)
        if vk_id:
            seen.append({
                'vk_id': vk_id,
                'first_name': user['full_name'],
                'last_name': '',
                'username': user['username'],
                'mapped_to': user_id_str,
                'last_seen': None
            })

    return jsonify({'status': 'success', 'seen': seen, 'users': users, 'user_map': vk_user_map})


@vk_chat_bp.route('/vk-load-members', methods=['POST'])
def api_load_vk_chat_members():
    """Загрузить участников чата VK через VK API"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403

    import json
    import vk_bot
    import urllib.request

    config = vk_bot.get_config()
    group_id = config.get('group_id')
    chat_peer_id = config.get('chat_peer_id')
    token = config.get('service_token') or config.get('token')

    if not group_id or not chat_peer_id or not token:
        return jsonify({'status': 'error', 'message': 'VK не настроен'}), 400

    # Получаем участников чата через messages.getConversationMembers
    url = f'https://api.vk.com/method/messages.getConversationMembers?peer_id={chat_peer_id}&v=5.131&access_token={token}'

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"VK API error (getConversationMembers): {e}")
        return jsonify({'status': 'error', 'message': f'Ошибка VK API: {str(e)}'}), 500

    if 'error' in data:
        error_msg = data['error'].get('error_msg', 'Неизвестная ошибка')
        logger.error(f"VK API error: {error_msg}")
        return jsonify({'status': 'error', 'message': f'VK API ошибка: {error_msg}'}), 400

    items = data.get('response', {}).get('items', [])
    
    if not items:
        return jsonify({'status': 'success', 'message': 'Участники не найдены', 'members': []})

    # Читаем текущий vk_user_map
    vk_config_path = os.path.join(DATA_DIR, 'vk_config.json')
    try:
        with open(vk_config_path, 'r', encoding='utf-8') as f:
            vk_config = json.load(f)
    except:
        vk_config = {'vk_user_map': {}}

    if 'vk_user_map' not in vk_config:
        vk_config['vk_user_map'] = {}

    # Добавляем новых участников
    added = []
    for member in items:
        vk_id = str(member.get('member_id'))
        
        # Пропускаем системные ID (чаты, боты)
        if not vk_id or vk_id.startswith('-') or vk_id == '0':
            continue
        
        # Получаем информацию о пользователе
        first_name = member.get('first_name', '')
        last_name = member.get('last_name', '')
        full_name = f'{first_name} {last_name}'.strip()
        
        if not full_name:
            full_name = f'VK Пользователь {vk_id}'

        # Если ещё не привязан
        if vk_id not in vk_config['vk_user_map']:
            # Ищем пользователя с таким именем в БД
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute('SELECT id, username, full_name FROM users WHERE full_name LIKE ?', (f'%{full_name}%',))
            row = cursor.fetchone()

            if row:
                # Нашли совпадение по имени
                vk_config['vk_user_map'][vk_id] = str(row['id'])
                added.append({
                    'vk_id': vk_id,
                    'full_name': full_name,
                    'mapped_to': row['id'],
                    'username': row['username']
                })
                logger.info(f"VK member auto-mapped: {vk_id} ({full_name}) -> user {row['id']}")
            else:
                # Не нашли - добавляем в список без привязки
                added.append({
                    'vk_id': vk_id,
                    'full_name': full_name,
                    'mapped_to': None,
                    'username': None
                })
                logger.info(f"VK member found: {vk_id} ({full_name}) - not mapped")

    # Сохраняем конфиг
    with open(vk_config_path, 'w', encoding='utf-8') as f:
        json.dump(vk_config, f, indent=2, ensure_ascii=False)

    logger.info(f"VK chat members loaded: {len(added)} total, {len([a for a in added if a.get('mapped_to')])} mapped")

    return jsonify({
        'status': 'success',
        'message': f'Загружено {len(added)} участников чата',
        'members': added
    })


@vk_chat_bp.route('/vk-user-map', methods=['POST'])
def api_save_vk_user_map():
    """Сохранить привязку VK ID к пользователю"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403

    import json

    data = request.json or {}
    vk_id = data.get('vk_id')
    user_id = data.get('user_id')  # может быть None для отвязки

    if not vk_id:
        return jsonify({'status': 'error', 'message': 'vk_id обязателен'}), 400

    # Читаем конфиг
    vk_config_path = os.path.join(DATA_DIR, 'vk_config.json')
    try:
        with open(vk_config_path, 'r', encoding='utf-8') as f:
            vk_config = json.load(f)
    except:
        return jsonify({'status': 'error', 'message': 'VK конфиг не найден'}), 404

    # Инициализируем vk_user_map если нет
    if 'vk_user_map' not in vk_config:
        vk_config['vk_user_map'] = {}

    # Обновляем привязку
    if user_id:
        vk_config['vk_user_map'][str(vk_id)] = str(user_id)
    else:
        # Удаляем привязку
        vk_config['vk_user_map'].pop(str(vk_id), None)

    # Сохраняем конфиг
    with open(vk_config_path, 'w', encoding='utf-8') as f:
        json.dump(vk_config, f, indent=2, ensure_ascii=False)

    logger.info(f"VK user map updated: vk_id={vk_id} -> user_id={user_id}")

    return jsonify({'status': 'success', 'message': 'Привязка сохранена'})
