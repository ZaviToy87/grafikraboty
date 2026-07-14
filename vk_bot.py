# -*- coding: utf-8 -*-
"""
VK Bot для GrafikRaboty - полная интеграция с ВКонтакте
Параллельная работа с Telegram ботом

Функции:
- Верификация пользователей через VK ID
- Отправка сообщений в чат сообщества
- Получение сообщений от пользователей
- Уведомления о запуске сервера
- Кнопки и callback-запросы
- Mapping VK user ID → пользователь в системе
"""
import json
import urllib.request
import ssl

# Отключаем проверку SSL для VK API (нужно для корпоративных сетей)
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE
import urllib.error
import urllib.parse
import hashlib
import hmac
import time
import threading
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

# Пути к файлам
try:
    from app_paths import DATA_DIR, BASE_DIR, LOGS_DIR
    VK_CONFIG_FILE = os.path.join(DATA_DIR, "vk_config.json")
    VK_LOG_FILE = os.path.join(LOGS_DIR, "vk_bot.log")
    VK_LAST_UPDATE_FILE = os.path.join(DATA_DIR, "vk_last_update_id.txt")
except ImportError:
    VK_CONFIG_FILE = "vk_config.json"
    VK_LOG_FILE = "vk_bot.log"
    VK_LAST_UPDATE_FILE = "vk_last_update_id.txt"
    DATA_DIR = "."
    BASE_DIR = "."
    LOGS_DIR = "logs"

# Глобальные переменные
_config = None
_last_update_id = 0
_message_handlers = []
_callback_handlers = []
_running = False
_long_poll_server = None
_long_poll_key = None
_long_poll_ts = None

# Rate limiting для уведомлений о сменах (чтобы не спамить)
_shift_notification_cooldown = {}  # {user_id: last_notification_time}
_SHIFT_NOTIFICATION_COOLDOWN_SEC = 60  # 1 минута между уведомлениями от одного пользователя


def log_message(message: str, level: str = "INFO"):
    """Записать сообщение в лог."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    try:
        # Создаём директорию если не существует
        log_dir = os.path.dirname(VK_LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(VK_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"  Не удалось записать в лог: {e}")


def load_vk_config() -> dict:
    """Загрузить конфигурацию VK."""
    global _config
    
    # Сначала пробуем загрузить из DATA_DIR
    if os.path.isfile(VK_CONFIG_FILE):
        try:
            with open(VK_CONFIG_FILE, "r", encoding="utf-8") as f:
                _config = json.load(f)
            log_message(f"VK конфигурация загружена из {VK_CONFIG_FILE}")
            return _config
        except Exception as e:
            log_message(f"Ошибка загрузки VK конфигурации: {e}", "ERROR")
    
    # Пробуем из BASE_DIR
    base_config = os.path.join(BASE_DIR, "vk_config.json")
    if os.path.isfile(base_config):
        try:
            with open(base_config, "r", encoding="utf-8") as f:
                _config = json.load(f)
            log_message(f"VK конфигурация загружена из {base_config}")
            # Копируем в DATA_DIR
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                import shutil
                shutil.copy2(base_config, VK_CONFIG_FILE)
            except Exception:
                pass
            return _config
        except Exception as e:
            log_message(f"Ошибка загрузки VK конфигурации из {base_config}: {e}", "ERROR")
    
    log_message("VK конфигурация не найдена (опционально)", "INFO")
    return {}


def get_config() -> dict:
    """Получить конфигурацию."""
    if _config is None:
        load_vk_config()
    return _config or {}


def _api_request(method: str, params: dict = None) -> dict:
    """Выполнить запрос к VK API."""
    config = get_config()
    token = config.get("service_token")
    api_version = config.get("api_version", "5.131")
    
    if not token:
        log_message("VK токен не настроен", "ERROR")
        return {}
    
    url = "https://api.vk.com/method/" + method
    params = params or {}
    params["access_token"] = token
    params["v"] = api_version
    
    try:
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as response:
            result = json.loads(response.read().decode("utf-8"))
            
        if "error" in result:
            log_message(f"VK API error: {result['error']}", "ERROR")
        return result.get("response", {})
    except Exception as e:
        log_message(f"VK API request error: {e}", "ERROR")
        return {}


def send_message(user_id: int = None, peer_id: int = None, message: str = "",
                 keyboard: dict = None, attachment: str = None, reply_to: int = None) -> bool:
    """
    Отправить сообщение пользователю или в чат.

    Args:
        user_id: ID пользователя (для личных сообщений)
        peer_id: ID чата/беседы/пользователя
        message: Текст сообщения
        keyboard: JSON клавиатуры
        attachment: Вложения (документы, фото и т.д.)
        reply_to: ID сообщения для ответа
    """
    config = get_config()
    group_id = config.get("group_id")

    if not config.get("service_token"):
        log_message("VK токен не настроен, сообщение не отправлено", "WARNING")
        return False

    params = {
        "message": message
    }

    if peer_id is not None:
        params["peer_id"] = peer_id
    elif user_id is not None:
        params["user_id"] = user_id
    else:
        # Отправка в чат сообщества (peer_id = 2000000000 + group_id для бесед)
        params["peer_id"] = 2000000000 + int(group_id)

    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)

    if attachment:
        params["attachment"] = attachment

    if reply_to:
        params["reply_to"] = reply_to

    # Для сервисных токенов random_id должен быть уникальным
    params["random_id"] = int(time.time() * 1000)

    result = _api_request("messages.send", params)

    if result:
        log_message(f"Сообщение отправлено (peer_id={peer_id or user_id})")
        return True

    return False


def upload_photo(file_path: str, peer_id: int = None, caption: str = "") -> bool:
    """
    Загрузить фото в чат с текстом (caption).

    Args:
        file_path: Путь к файлу
        peer_id: ID чата (опционально)
        caption: Текст сообщения вместе с фото

    Returns:
        True если успешно
    """
    config = get_config()
    group_id = config.get("group_id")

    if not config.get("service_token"):
        log_message("VK токен не настроен", "ERROR")
        return False

    # 1. Получаем URL для загрузки
    upload_url_data = _api_request("photos.getMessagesUploadServer", {
        "peer_id": peer_id or (2000000000 + int(group_id))
    })

    if not upload_url_data or 'upload_url' not in upload_url_data:
        log_message("Не удалось получить URL для загрузки фото", "ERROR")
        return False

    upload_url = upload_url_data['upload_url']

    # 2. Загружаем файл
    try:
        import urllib.request
        import mimetypes

        boundary = "----WebKitFormBoundary" + str(time.time()).replace('.', '')

        with open(file_path, 'rb') as f:
            file_data = f.read()

        content_type = mimetypes.guess_type(file_path)[0] or 'image/jpeg'

        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"photo\"; filename=\"{os.path.basename(file_path)}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode('utf-8') + file_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        req = urllib.request.Request(
            upload_url,
            data=body,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
        )

        # Используем SSL-контекст без проверки сертификата
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

        # 3. Сохраняем фото
        if result.get('photo') and result.get('hash') and result.get('server'):
            save_data = _api_request("photos.saveMessagesPhoto", {
                "photo": result['photo'],
                "hash": result['hash'],
                "server": result['server']
            })

            if save_data and len(save_data) > 0:
                photo_id = f"photo{save_data[0]['owner_id']}_{save_data[0]['id']}"
                # Отправляем фото + текст в чат
                return send_message(peer_id=peer_id, message=caption, attachment=photo_id)

        return False
    except Exception as e:
        log_message(f"Ошибка загрузки фото: {e}", "ERROR")
        return False


def upload_document(file_path: str, peer_id: int = None, caption: str = "") -> bool:
    """
    Загрузить документ в чат с текстом (caption).

    Args:
        file_path: Путь к файлу
        peer_id: ID чата (опционально)
        caption: Текст сообщения вместе с документом

    Returns:
        True если успешно
    """
    config = get_config()
    group_id = config.get("group_id")

    if not config.get("service_token"):
        log_message("VK токен не настроен", "ERROR")
        return False

    # 1. Получаем URL для загрузки (type: doc для групп)
    upload_url_data = _api_request("docs.getMessagesUploadServer", {
        "peer_id": peer_id or (2000000000 + int(group_id)),
        "type": "doc"  # Для групп используем doc
    })

    if not upload_url_data or 'upload_url' not in upload_url_data:
        log_message(f"Не удалось получить URL для загрузки документа. Ответ VK: {upload_url_data}", "ERROR")
        return False

    upload_url = upload_url_data['upload_url']
    log_message(f"VK document upload URL получен: {upload_url[:50]}...", "INFO")

    # 2. Загружаем файл
    try:
        import urllib.request
        import mimetypes

        boundary = "----WebKitFormBoundary" + str(time.time()).replace('.', '')

        with open(file_path, 'rb') as f:
            file_data = f.read()

        content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        filename = os.path.basename(file_path)

        log_message(f"VK document: загружаем {filename} ({len(file_data)} байт)", "INFO")

        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode('utf-8') + file_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        req = urllib.request.Request(
            upload_url,
            data=body,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
        )

        # Используем SSL-контекст без проверки сертификата
        with urllib.request.urlopen(req, timeout=30, context=_ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

        log_message(f"VK document upload result: {result}", "INFO")

        # 3. Сохраняем документ
        if result.get('file'):
            save_data = _api_request("docs.save", {
                "file": result['file']
            })

            log_message(f"VK document save result: {save_data}", "INFO")

            if save_data:
                # VK API возвращает {'type': 'doc', 'doc': {...}} а не список
                doc_info = save_data.get('doc') or (save_data[0] if isinstance(save_data, list) and len(save_data) > 0 else None)
                
                if doc_info:
                    doc_id = f"doc{doc_info['owner_id']}_{doc_info['id']}"
                    log_message(f"VK document saved: {doc_id}", "INFO")
                    # Отправляем документ + текст в чат
                    return send_message(peer_id=peer_id, message=caption, attachment=doc_id)

        log_message("VK document: не удалось сохранить документ", "WARNING")
        return False
    except Exception as e:
        log_message(f"Ошибка загрузки документа: {e}", "ERROR")
        import traceback
        log_message(traceback.format_exc(), "ERROR")
        return False


def send_broadcast(message: str, keyboard: dict = None, attachment: str = None):
    """Отправить сообщение всем подписчикам сообщества."""
    config = get_config()
    group_id = config.get("group_id")
    
    if not group_id:
        return False
    
    # Получаем список подписчиков
    subscribers = _api_request("groups.getMembers", {
        "group_id": group_id,
        "fields": "id",
        "count": 100
    })
    
    if not subscribers or "items" not in subscribers:
        return False
    
    sent_count = 0
    for user in subscribers.get("items", [])[:50]:  # Ограничим 50 для безопасности
        user_id = user.get("id")
        if user_id:
            if send_message(user_id=user_id, message=message, keyboard=keyboard, attachment=attachment):
                sent_count += 1
            time.sleep(0.5)  # Пауза между сообщениями
    
    log_message(f"Broadcast отправлен {sent_count} пользователям")
    return sent_count


def create_keyboard(buttons: List[List[dict]], inline: bool = True) -> dict:
    """
    Создать клавиатуру для сообщений.
    Для VK API inline кнопок с open_link label должна быть ВНУТРИ action.

    Args:
        buttons: Список списков кнопок [[{label, action}], ...]
        inline: True для inline клавиатуры, False для обычной

    Returns:
        JSON клавиатуры для VK API
    """
    keyboard = {
        "one_time": False,
        "inline": inline,
        "buttons": []
    }

    for row in buttons:
        button_row = []
        for btn in row:
            action_type = btn.get("action", "text")
            
            # Для open_link кнопок - label ВНУТРИ action
            if action_type == "open_link":
                button = {
                    "action": {
                        "type": "open_link",
                        "link": btn.get("url", ""),
                        "label": btn.get("label", "Открыть")
                    }
                }
            else:
                button = {
                    "action": {
                        "type": action_type
                    }
                }
                
                if action_type == "text":
                    button["action"]["label"] = btn.get("label", "Button")
                    button["action"]["payload"] = json.dumps(btn.get("payload", {}))
                elif action_type == "callback":
                    button["action"]["label"] = btn.get("label", "Button")
                    button["action"]["payload"] = json.dumps(btn.get("payload", {}))
                elif action_type == "vkpay":
                    button["action"]["hash"] = btn.get("hash", "")

            button_row.append(button)

        keyboard["buttons"].append(button_row)

    return keyboard


def answer_callback(event_id: str, user_id: int, message: str = "", 
                    show_alert: bool = False, link: str = None):
    """Ответ на callback-запрос от кнопки."""
    config = get_config()
    group_id = config.get("group_id")
    
    params = {
        "event_id": event_id,
        "user_id": user_id,
        "group_id": group_id,
        "message": message,
        "show_alert": 1 if show_alert else 0
    }
    
    if link:
        params["link"] = link
    
    result = _api_request("messages.sendMessageEventAnswer", params)
    return bool(result)


def get_user_info(user_id: int) -> dict:
    """Получить информацию о пользователе VK."""
    result = _api_request("users.get", {
        "user_ids": user_id,
        "fields": "first_name,last_name,photo_100,city,country"
    })
    
    if result and len(result) > 0:
        return result[0]
    return {}


def vk_id_to_user_id(vk_id: int) -> Optional[int]:
    """Преобразовать VK ID в ID пользователя в системе."""
    config = get_config()
    user_map = config.get("vk_user_map", {})
    
    # Проверяем прямой маппинг
    if str(vk_id) in user_map:
        return user_map[str(vk_id)]
    
    # Проверяем как int
    if vk_id in user_map:
        return user_map[vk_id]
    
    return None


def user_id_to_vk_id(user_id: int) -> Optional[int]:
    """Преобразовать ID пользователя в системе в VK ID."""
    config = get_config()
    user_map = config.get("vk_user_map", {})
    
    for vk_uid, uid in user_map.items():
        if uid == user_id:
            return int(vk_uid)
    
    return None


def add_vk_user_mapping(vk_id: int, user_id: int):
    """Добавить маппинг VK ID → пользователь в системе."""
    config = get_config()
    
    if "vk_user_map" not in config:
        config["vk_user_map"] = {}
    
    config["vk_user_map"][str(vk_id)] = user_id
    
    # Сохраняем конфигурацию
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(VK_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        log_message(f"Добавлен VK маппинг: {vk_id} → {user_id}")
    except Exception as e:
        log_message(f"Ошибка сохранения VK маппинга: {e}", "ERROR")


def on_message(handler: Callable):
    """Декоратор для регистрации обработчика сообщений."""
    _message_handlers.append(handler)
    return handler


def on_callback(handler: Callable):
    """Декоратор для регистрации обработчика callback-запросов."""
    _callback_handlers.append(handler)
    return handler


def _process_message_event(event_data: dict):
    """Обработать событие нового сообщения."""
    # ВАЖНО: В Long Poll v5.208 структура может отличаться
    # Пробуем разные варианты извлечения сообщения
    
    # Вариант 1: message прямо в event_data
    message = event_data.get("message", {})
    
    # Вариант 2: message в object.message
    if not message:
        object_data = event_data.get("object", {})
        message = object_data.get("message", {})
    
    # Вариант 3: event_data - это и есть message
    if not message and "from_id" in event_data:
        message = event_data
    
    text = message.get("text", "").strip()
    from_id = message.get("from_id")
    peer_id = message.get("peer_id")
    conversation_message_id = message.get("conversation_message_id")
    message_id = message.get("id")  # ID сообщения для получения через API
    
    log_message(f"VK message structure: from_id={from_id}, peer_id={peer_id}, text='{text[:30]}'", "DEBUG")
    
    # Получаем вложения из message И из event_data (VK может присылать в обоих местах)
    attachments = message.get("attachments", [])
    if not attachments:
        # Пробуем получить из корня event_data (для нескольких вложений)
        attachments = event_data.get("attachments", [])
    
    # Проверяем object.message.attachments (VK API v5.131)
    if not attachments:
        object_data = event_data.get("object", {})
        obj_message = object_data.get("message", {})
        attachments = obj_message.get("attachments", [])
    
    # ВАЖНО: VK Long Poll может не передавать все вложения
    # Если вложений мало (0-1), но сообщение должно иметь больше - получаем через API
    config = get_config()
    service_token = config.get("service_token")
    
    # Получаем conversation_message_id для API вызова
    conv_message_id = message.get("conversation_message_id")  # ID сообщения в диалоге
    
    log_message(f"VK API check: service_token={bool(service_token)}, len(attachments)={len(attachments)}, conv_message_id={conv_message_id}, peer_id={peer_id}", "DEBUG")
    
    if service_token and len(attachments) <= 1 and conv_message_id and peer_id:
        log_message(f"VK API: Getting full message via messages.getByConversationMessageId...", "INFO")
        try:
            import urllib.request
            # Получаем полное сообщение через messages.getByConversationMessageId
            api_url = f"https://api.vk.com/method/messages.getByConversationMessageId?peer_id={peer_id}&conversation_message_ids={conv_message_id}&access_token={service_token}&v=5.131"
            log_message(f"VK API URL: {api_url[:100]}...", "DEBUG")
            req = urllib.request.Request(api_url)
            with urllib.request.urlopen(req, timeout=5, context=_ssl_context) as resp:
                api_result = json.loads(resp.read().decode('utf-8'))
                log_message(f"VK API response: {api_result}", "DEBUG")
                if 'response' in api_result:
                    response = api_result['response']
                    messages_list = response.get('items', [])
                    if messages_list:
                        full_message = messages_list[0]
                        api_attachments = full_message.get('attachments', [])
                        
                        # Проверяем пересланные сообщения (fwd_messages)
                        fwd_messages = full_message.get('fwd_messages', [])
                        for fwd_msg in fwd_messages:
                            fwd_attachments = fwd_msg.get('attachments', [])
                            if fwd_attachments:
                                log_message(f"VK API: Found {len(fwd_attachments)} attachments in forwarded message", "INFO")
                                api_attachments.extend(fwd_attachments)
                        
                        log_message(f"VK API: Found {len(api_attachments)} attachments in API response", "INFO")
                        if len(api_attachments) > len(attachments):
                            log_message(f"VK API: Found {len(api_attachments)} attachments (Long Poll sent {len(attachments)})", "INFO")
                            attachments = api_attachments
                        else:
                            log_message(f"VK API: API also returned {len(api_attachments)} attachments (same as Long Poll)", "INFO")
        except Exception as e:
            log_message(f"VK API error getting full message: {e}", "WARNING")
    
    # Логируем полную структуру для отладки
    log_message(f"VK event_data keys: {list(event_data.keys())}", "DEBUG")
    log_message(f"VK message keys: {list(message.keys())}", "DEBUG")
    log_message(f"VK attachments count: {len(attachments)}", "DEBUG")
    
    # Если вложений много, логируем их типы
    if len(attachments) > 1:
        log_message(f"VK MULTIPLE ATTACHMENTS: {len(attachments)} files", "INFO")
        for i, att in enumerate(attachments):
            att_type = att.get('type', 'unknown')
            log_message(f"  Attachment {i+1}: type={att_type}", "INFO")
    
    # Логируем ВСЮ структуру для первого вложения (для отладки)
    if attachments:
        log_message(f"VK First attachment: {attachments[0]}", "DEBUG")

    if from_id < 0:  # Игнорируем сообщения от ботов
        return

    log_message(f"Сообщение от VK {from_id}: {text[:50]}...")

    # Проверяем, есть ли пользователь в системе
    user_id = vk_id_to_user_id(abs(from_id))

    # Синхронизация выполняется в default_message_handler
    # Здесь не отправляем чтобы избежать дублирования

    # Вызываем обработчики
    for handler in _message_handlers:
        try:
            handler(
                vk_id=abs(from_id),
                user_id=user_id,
                peer_id=peer_id,
                message=text,
                message_id=conversation_message_id,
                attachments=attachments,
                event_data=event_data
            )
        except Exception as e:
            log_message(f"Ошибка в обработчике сообщения: {e}", "ERROR")


def _process_callback_event(event_data: dict):
    """Обработать событие callback-запроса от кнопки."""
    callback = event_data.get("message", {})
    payload = callback.get("payload")
    from_id = callback.get("from_id")
    conversation_message_id = callback.get("conversation_message_id")
    event_id = event_data.get("event_id")
    
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}
    
    log_message(f"Callback от VK {from_id}: {payload}")
    
    user_id = vk_id_to_user_id(abs(from_id))
    
    for handler in _callback_handlers:
        try:
            handler(
                vk_id=abs(from_id),
                user_id=user_id,
                payload=payload,
                event_id=event_id,
                message_id=conversation_message_id,
                event_data=event_data
            )
        except Exception as e:
            log_message(f"Ошибка в обработчике callback: {e}", "ERROR")


def _init_long_poll() -> bool:
    """Инициализировать Long Poll сервер."""
    global _long_poll_server, _long_poll_key, _long_poll_ts
    
    config = get_config()
    group_id = config.get("group_id")
    
    if not group_id:
        log_message("VK group_id не настроен", "ERROR")
        return False
    
    result = _api_request("groups.getLongPollServer", {
        "group_id": group_id
    })
    
    if result:
        _long_poll_server = result.get("server")
        _long_poll_key = result.get("key")
        _long_poll_ts = result.get("ts")
        log_message(f"VK Long Poll инициализирован: {_long_poll_server}")
        return True
    
    return False


def _long_poll_loop():
    """Основной цикл Long Poll."""
    global _running, _long_poll_ts, _long_poll_server, _long_poll_key

    while _running:
        if not _long_poll_server or not _long_poll_key:
            if not _init_long_poll():
                time.sleep(5)
                continue

        try:
            # ВАЖНО: version=5.208 для Callback API (не version=3!)
            url = f"{_long_poll_server}?act=a_check&key={_long_poll_key}&ts={_long_poll_ts}&wait=25&version=5.208"
            req = urllib.request.Request(url)

            # Используем SSL-контекст без проверки сертификата (как для VK API)
            with urllib.request.urlopen(req, timeout=30, context=_ssl_context) as response:
                data = json.loads(response.read().decode("utf-8"))

            # Проверяем failed (Long Poll нужно переинициализировать)
            if data.get('failed'):
                log_message(f"Long Poll failed (код {data.get('failed')}), переинициализация...", "WARNING")
                _long_poll_server = None
                _long_poll_key = None
                _long_poll_ts = None
                continue

            _long_poll_ts = data.get("ts", _long_poll_ts)

            # Логируем все события для отладки
            updates = data.get("updates", [])
            if updates:
                log_message(f"Long Poll: получено {len(updates)} событий", "INFO")
            
            for event in updates:
                event_type = event.get("type")
                event_obj = event.get("object", {})
                
                # В версии 5.208 структура может отличаться
                message_data = event_obj.get("message", event_obj)
                
                log_message(f"Long Poll event: type={event_type}, from_id={message_data.get('from_id', '?')}", "DEBUG")

                if event_type == "message_new":
                    _process_message_event(event_obj)
                elif event_type == "message_reply":
                    pass  # Можно обработать ответ
                elif event_type == "message_allow":
                    log_message(f"Пользователь {message_data.get('user_id')} разрешил сообщения")
                elif event_type == "message_deny":
                    log_message(f"Пользователь {message_data.get('user_id')} запретил сообщения")
                elif event_type == "message_edit":
                    log_message(f"Сообщение отредактировано")
                else:
                    log_message(f"Long Poll: неизвестное событие {event_type}")  # DEBUG
            
        except urllib.error.URLError as e:
            log_message(f"Long Poll ошибка соединения: {e}", "WARNING")
            _long_poll_server = None  # Переинициализация
        except Exception as e:
            log_message(f"Long Poll ошибка: {e}", "ERROR")
            time.sleep(1)


def start_polling():
    """Запустить опрос Long Poll сервера."""
    global _running
    
    if _running:
        log_message("VK polling уже запущен", "WARNING")
        return
    
    config = get_config()
    if not config.get("service_token"):
        log_message("VK токен не настроен, polling не запущен", "INFO")
        return
    
    log_message("Запуск VK Long Polling...")
    _running = True
    
    if not _init_long_poll():
        log_message("Не удалось инициализировать VK Long Poll", "ERROR")
        _running = False
        return
    
    # Запускаем в отдельном потоке
    poll_thread = threading.Thread(target=_long_poll_loop, daemon=True)
    poll_thread.start()
    log_message("VK Long Polling запущен в фоновом режиме")


def stop_polling():
    """Остановить опрос Long Poll сервера."""
    global _running
    _running = False
    log_message("VK Long Polling остановлен")


def send_startup_notification(tunnel_url: str, password: str, link_local: str,
                              local_ip: str, schedule_text: str = "", reminders_text: str = ""):
    """
    Отправить уведомление о запуске сервера v2.0 — КОНТРАСТНОЕ И ЯРКОЕ.
    """
    config = get_config()
    group_id = config.get("group_id")
    admin_vk_id = config.get("admin_vk_id")
    chat_peer_id = config.get("chat_peer_id")
    
    if not config.get("service_token"):
        return False
    
    # Получаем актуальный публичный IP
    public_ip = get_public_ip() or local_ip
    
    # 🔥 НОВОЕ ФОРМАТИРОВАНИЕ v2.0
    msg = (
        f"🚀 *СЕРВЕР ЗАПУЩЕН — ВЕРСИЯ 2.0* 🚀\n\n"
        
        f"⏰ *Время запуска:* {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *ПОСТОЯННАЯ ССЫЛКА:*\n"
        f"`{link_local}/get-tunnel-link`\n\n"
        
        f"🔐 *ПАРОЛЬ:* `{public_ip}`\n"
        f"_(это ваш внешний IP — не меняется)_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"🌐 *ТУННЕЛЬ:*\n"
        f"`{tunnel_url}`\n\n"
        
        f"📍 *ЛОКАЛЬНАЯ СЕТЬ (Wi-Fi):*\n"
        f"👉 `{link_local}`\n\n"
        
        f"🌍 *ВНЕШНИЙ IP (проброс):*\n"
        f"👉 `http://{public_ip}:8080`\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 *СОТРУДНИКАМ:*\n"
        f"• Дома (Wi-Fi): {link_local}\n"
        f"• Извне (туннель): {tunnel_url}\n"
        f"• Извне (проброс): http://{public_ip}:8080\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if schedule_text:
        msg += f"\n{schedule_text}\n"
    else:
        msg += "\n📋 *Сегодня в графике:* записей нет\n"
    
    if reminders_text:
        msg += f"\n{reminders_text}\n"
    
    msg += (
        f"\n📊 *Мониторинг:*\n"
        f"• Статус туннеля: {link_local}/tunnel-status\n"
        f"• Автоперезапуск: включён (проверка каждые 30 сек)\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *БЫСТРЫЙ ДОСТУП:*\n"
        f"• Открыть график: {link_local}\n"
        f"• Статус туннеля: {link_local}/tunnel-status\n\n"
        
        f"✅ *v2.0 — Все IP актуальны!*"
    )
    
    # Отправляем администратору
    if admin_vk_id:
        send_message(user_id=int(admin_vk_id), message=msg)
        log_message("VK уведомление отправлено администратору (v2.0)")
    
    # Отправляем в чат сообщества
    if chat_peer_id:
        send_message(peer_id=int(chat_peer_id), message=msg)
        log_message("VK уведомление отправлено в чат (v2.0)")
    
    return True
    chat_peer_id = config.get('chat_peer_id')
    if chat_peer_id:
        send_message(peer_id=int(chat_peer_id), message=msg, keyboard=keyboard)
        log_message(f"VK уведомление отправлено в чат сообщества (peer_id={chat_peer_id})")
    
    return True


def send_tunnel_restart_notification(tunnel_url: str, password: str, restart_count: int):
    """Отправить уведомление о перезапуске туннеля с ПРАВИЛЬНЫМИ IP (v2.0)."""
    config = get_config()
    admin_vk_id = config.get("admin_vk_id")
    
    if not admin_vk_id:
        return False
    
    # Получаем актуальные IP
    local_ip = get_local_ip()
    public_ip = get_public_ip() or local_ip
    
    # 🔥 НОВОЕ ФОРМАТИРОВАНИЕ v2.0 - КОНТРАСТНОЕ И ЯРКОЕ
    msg = (
        f"🚀 *СЕРВЕР ЗАПУЩЕН — ВЕРСИЯ 2.0* 🚀\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 *ТУННЕЛЬ (интернет):*\n"
        f"`{tunnel_url}`\n"
        f"🔐 Пароль: `{password}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"📍 *ЛОКАЛЬНАЯ СЕТЬ (Wi-Fi):*\n"
        f"👉 `http://{local_ip}:8080`\n\n"
        
        f"🌍 *ВНЕШНИЙ IP (проброс):*\n"
        f"👉 `http://{public_ip}:8080`\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 *СОТРУДНИКАМ:*\n"
        f"• Дома (Wi-Fi): http://{local_ip}:8080\n"
        f"• Извне: {tunnel_url}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"✅ *v2.0 — Все IP актуальны!*"
    )
    
    send_message(user_id=int(admin_vk_id), message=msg)
    return True


def send_tunnel_error(message: str, restart_count: int):
    """Отправить уведомление об ошибке туннеля."""
    config = get_config()
    admin_vk_id = config.get("admin_vk_id")
    
    if not admin_vk_id:
        return False
    
    msg = (
        f"❌ *Туннель недоступен!*\n\n"
        f"Превышен лимит перезапусков ({restart_count}).\n\n"
        f"Ошибка: {message}\n\n"
        f"Требуется ручное вмешательство:\n"
        f"• Проверьте интернет\n"
        f"• Проверьте, запущен ли сервер\n"
        f"• Перезапустите вручную"
    )
    
    send_message(user_id=int(admin_vk_id), message=msg)
    return True


# Обработчики по умолчанию
@on_message
def default_message_handler(vk_id: int, user_id: Optional[int], peer_id: int,
                           message: str, message_id: int, attachments: list = None,
                           event_data: dict = None):
    """Обработчик сообщений по умолчанию."""
    config = get_config()
    admin_vk_id = config.get("admin_vk_id")

    # Проверяем что это из чата группы (peer_id >= 2000000000)
    if peer_id and peer_id >= 2000000000:
        # Отправляем на синхронизацию через HTTP
        # ВСЯ обработка (вложения + текст) выполняется в web_vk_chat.py
        log_message(f"VK MSG: peer_id={peer_id}, from_id={event_data.get('message', {}).get('from_id') if event_data else 'N/A'}, text='{message[:50]}...', attachments={len(attachments) if attachments else 0}")
        try:
            import urllib.request
            sync_url = 'http://127.0.0.1:8080/api/vk-chat/vk-sync'
            # ВАЖНО: передаём attachments для обработки вложений
            sync_data = {'event': event_data, 'attachments': attachments or []}
            log_message(f"VK SYNC: sending {len(attachments) if attachments else 0} attachments, event_keys={list(event_data.keys()) if event_data else 'N/A'}")
            data = json.dumps(sync_data).encode('utf-8')
            req = urllib.request.Request(
                sync_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                log_message(f"VK сообщение синхронизировано: {result}")
        except Exception as e:
            log_message(f"Ошибка синхронизации VK: {e}", "ERROR")

    # Команды
    if message.lower() == "/start":
        send_message(
            peer_id=peer_id,
            message=(
                "👋 Привет! Я бот ГрафикРаботы.\n\n"
                "📋 *Доступные команды:*\n"
                "/start - Начать работу\n"
                "/help - Помощь\n"
                "/address - Все адреса доступа 🔗\n"
                "/tunnel - Информация о туннеле 🔒\n"
                "/status - Статус сервера 📊\n"
                "/schedule - Расписание на сегодня\n"
                "/link - Ссылка для подключения"
            )
        )
        return

    if message.lower() == "/help":
        send_message(
            peer_id=peer_id,
            message=(
                "📖 *Помощь*\n\n"
                "Этот бот помогает управлять графиком работы.\n\n"
                "Вы можете:\n"
                "• Просматривать расписание\n"
                "• Получать уведомления\n"
                "• Подключаться к системе\n\n"
                "Для веб-доступа используйте команду /link"
            )
        )
        return

    if message.lower() == "/link":
        # Старая команда - перенаправляет на /address
        handle_address_command(peer_id)
        return

    if message.lower() == "/address":
        handle_address_command(peer_id)
        return

    if message.lower() == "/tunnel":
        handle_tunnel_command(peer_id)
        return

    if message.lower() == "/status":
        handle_status_command(peer_id)
        return

    # Если пользователь не найден в системе
    if user_id is None and admin_vk_id and vk_id == int(admin_vk_id):
        # Админ пишет - можно добавить логику
        pass


def handle_address_command(peer_id):
    """Отправить сообщение со всеми актуальными адресами доступа"""
    import json
    import os
    
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    # Читаем tunnel_info.json
    tunnel_url = ""
    tunnel_password = ""
    tunnel_info_path = os.path.join(DATA_DIR, 'tunnel_info.json')
    if not os.path.exists(tunnel_info_path):
        tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
    
    if os.path.exists(tunnel_info_path):
        try:
            with open(tunnel_info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            tunnel_url = info.get('tunnel_url', '')
            tunnel_password = info.get('password', '')
        except:
            pass
    
    # Формируем сообщение
    msg = (
        "🌐 *АКТУАЛЬНЫЕ АДРЕСА ДОСТУПА*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📍 *ВАРИАНТ 1: Внешний IP (РЕКОМЕНДУЕТСЯ)*\n"
        f"`http://{public_ip}:8080`\n"
        f"Пароль: `{public_ip}`\n\n"
        "📍 *ВАРИАНТ 2: Локальная сеть (Wi-Fi)*\n"
        f"`http://{local_ip}:8080`\n"
        f"Пароль: не требуется\n\n"
        "📍 *ВАРИАНТ 3: Туннель (резерв)*\n"
    )
    
    if tunnel_url:
        msg += (
            f"`{tunnel_url}`\n"
            f"Пароль: `{tunnel_password}`\n\n"
        )
    else:
        msg += "⚠️ Туннель не активен\n\n"
    
    msg += (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Рекомендация:*\n"
        "Используй внешний IP — это надёжнее!\n"
        "Туннель может быть недоступен временно.\n\n"
        "📱 *Скопируй и вставь в браузер:*\n"
        f"http://{public_ip}:8080"
    )
    
    # Отправляем сообщение
    send_message(peer_id=peer_id, message=msg)
    
    # Отправляем клавиатуру с кнопками
    keyboard = {
        "inline": [
            [
                {
                    "action": "open_link",
                    "label": "🌐 Открыть внешний IP",
                    "url": f"http://{public_ip}:8080"
                }
            ],
            [
                {
                    "action": "open_link",
                    "label": "📶 Локальная сеть",
                    "url": f"http://{local_ip}:8080"
                }
            ]
        ]
    }
    
    if tunnel_url:
        keyboard["inline"].append([
            {
                "action": "open_link",
                "label": "🔒 Туннель",
                "url": tunnel_url
            }
        ])
    
    # Отправляем клавиатуру отдельным сообщением
    try:
        config = get_config()
        token = config.get('service_token')
        if token:
            url = f"https://api.vk.com/method/messages.send?peer_id={peer_id}&message=Выберите способ подключения:&keyboard={urllib.parse.quote(json.dumps(keyboard, ensure_ascii=False))}&random_id={int(time.time() * 1000)}&access_token={token}&v=5.131"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as resp:
                pass
    except Exception as e:
        log_message(f"Ошибка отправки клавиатуры: {e}", "ERROR")


def handle_tunnel_command(peer_id):
    """Отправить информацию только о туннеле"""
    import json
    import os
    
    tunnel_info_path = os.path.join(DATA_DIR, 'tunnel_info.json')
    if not os.path.exists(tunnel_info_path):
        tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
    
    if os.path.exists(tunnel_info_path):
        try:
            with open(tunnel_info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            tunnel_url = info.get('tunnel_url', '')
            tunnel_password = info.get('password', '')
            
            msg = (
                "🔒 *ИНФОРМАЦИЯ О ТУННЕЛЕ*\n\n"
                f"URL: `{tunnel_url}`\n"
                f"Пароль: `{tunnel_password}`\n\n"
                "⚠️ Если туннель не работает (ошибка 503):\n"
                "1. Обновите страницу (F5)\n"
                "2. Используйте внешний IP: /address\n"
                "3. Попробуйте позже — туннель перезапустится\n\n"
                "💡 Совет: внешний IP надёжнее!"
            )
            
            send_message(peer_id=peer_id, message=msg)
            
            # Кнопка для открытия туннеля
            keyboard = {
                "inline": [
                    [
                        {
                            "action": "open_link",
                            "label": "🔓 Открыть туннель",
                            "url": tunnel_url
                        }
                    ]
                ]
            }
            
            config = get_config()
            token = config.get('service_token')
            if token:
                url = f"https://api.vk.com/method/messages.send?peer_id={peer_id}&message=Нажмите кнопку для открытия:&keyboard={urllib.parse.quote(json.dumps(keyboard, ensure_ascii=False))}&random_id={int(time.time() * 1000)}&access_token={token}&v=5.131"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as resp:
                    pass
        except Exception as e:
            send_message(peer_id=peer_id, message="⚠️ Туннель не найден в tunnel_info.json\n\nИспользуйте /address для других способов доступа")
    else:
        send_message(peer_id=peer_id, message="⚠️ Туннель не активен\n\nИспользуйте /address для доступа через внешний IP")


def handle_status_command(peer_id):
    """Отправить статус сервера и доступности"""
    import socket
    
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    # Проверяем локальный сервер
    server_ok = False
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 8080))
        sock.close()
        server_ok = (result == 0)
    except:
        pass
    
    # Проверяем туннель
    tunnel_status = "⚠️ Не активен"
    tunnel_info_path = os.path.join(DATA_DIR, 'tunnel_info.json')
    if not os.path.exists(tunnel_info_path):
        tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
    
    if os.path.exists(tunnel_info_path):
        try:
            with open(tunnel_info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            tunnel_url = info.get('tunnel_url', '')
            if tunnel_url:
                # Пробуем проверить туннель
                try:
                    req = urllib.request.Request(f"{tunnel_url}/login", headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5, context=_ssl_context) as r:
                        if r.status == 200 or r.status == 302:
                            tunnel_status = "✅ Активен"
                        else:
                            tunnel_status = f"⚠️ Статус {r.status}"
                except:
                    tunnel_status = "❌ Недоступен"
        except:
            pass
    
    msg = (
        "📊 *СТАТУС СЕРВЕРА*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🖥️ Локальный сервер: {'✅ Работает' if server_ok else '❌ Не работает'}\n"
        f"📍 Локальный IP: `{local_ip}`\n"
        f"🌍 Внешний IP: `{public_ip}`\n"
        f"🔒 Туннель: {tunnel_status}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 Для доступа используйте:\n"
        f"`http://{public_ip}:8080`\n\n"
        "Команда /address — все варианты доступа"
    )
    
    send_message(peer_id=peer_id, message=msg)


@on_callback
def default_callback_handler(vk_id: int, user_id: Optional[int], payload: dict,
                            event_id: str, message_id: int, event_data: dict):
    """Обработчик callback-запросов по умолчанию."""
    action = payload.get("action")
    
    if action == "get_link":
        answer_callback(event_id, vk_id, message="Ссылка отправлена!")
    elif action == "refresh":
        answer_callback(event_id, vk_id, message="Обновлено!")


def get_local_ip():
    """Получить локальный IP адрес в сети (кэшируем результат)"""
    import socket
    if hasattr(get_local_ip, '_cached'):
        return get_local_ip._cached
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        get_local_ip._cached = ip
        return ip
    except Exception:
        get_local_ip._cached = "127.0.0.1"
        return "127.0.0.1"


def get_public_ip():
    """Получить внешний IP адрес (кэшируем на 5 минут)"""
    import time
    
    # Проверяем кэш (5 минут)
    if hasattr(get_public_ip, '_cached') and hasattr(get_public_ip, '_cached_time'):
        if time.time() - get_public_ip._cached_time < 300:  # 5 минут
            return get_public_ip._cached
    
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8, context=_ssl_context) as r:
                ip = (r.read().decode() or "").strip()
                if ip and len(ip) < 20:
                    get_public_ip._cached = ip
                    get_public_ip._cached_time = time.time()
                    return ip
        except Exception:
            continue
    
    # Если не получилось — возвращаем локальный
    get_public_ip._cached = get_local_ip()
    get_public_ip._cached_time = time.time()
    return get_public_ip._cached


def send_shift_notification(shift_action, user_name, shift_data):
    """
    Отправить уведомление администратору о открытии/закрытии смены с полным отчётом
    Rate limiting: не чаще 1 раза в 60 секунд от одного пользователя

    Args:
        shift_action: 'open' или 'close'
        user_name: Имя сотрудника
        shift_data: dict с данными смены
    """
    global _shift_notification_cooldown, _SHIFT_NOTIFICATION_COOLDOWN_SEC
    
    config = get_config()
    admin_vk_id = config.get("admin_vk_id")

    if not config.get("service_token") or not admin_vk_id:
        return False

    # Rate limiting: проверяем cooldown
    import time
    current_time = time.time()
    user_key = f"{user_name}_{shift_action}"
    
    if user_key in _shift_notification_cooldown:
        last_time = _shift_notification_cooldown[user_key]
        if current_time - last_time < _SHIFT_NOTIFICATION_COOLDOWN_SEC:
            log_message(f"Shift notification skipped (cooldown): {user_name} - {shift_action}", "WARNING")
            return False
    
    # Обновляем cooldown
    _shift_notification_cooldown[user_key] = current_time
    log_message(f"Shift notification allowed: {user_name} - {shift_action}")

    # Формируем сообщение
    if shift_action == 'open':
        msg = (
            f"🔔 ОТКРЫТИЕ СМЕНЫ\n"
            f"{'━' * 30}\n"
            f"👤 Сотрудник: {user_name}\n"
            f"📅 Дата: {shift_data.get('day', 0)}.{shift_data.get('month', 0)}.{shift_data.get('year', 0)}\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M')}\n"
            f"💰 Касса: {shift_data.get('morning_cash', 0)} руб.\n"
            f"{'━' * 30}\n"
            f"✅ Смена открыта. Удачной смены!"
        )
    else:  # close
        revenue = round(float(shift_data.get('revenue_total', 0)), 2)
        acquiring_kkt = round(float(shift_data.get('acquiring_amount', 0)), 2)
        terminal_actual = round(float(shift_data.get('terminal_actual', 0)), 2)
        evening_cash = round(float(shift_data.get('evening_cash', 0)), 2)
        evening_cashless = round(float(shift_data.get('evening_cashless', 0)), 2)
        discrepancy = round(float(shift_data.get('discrepancy', 0)), 2)
        morning_cash = round(float(shift_data.get('morning_cash', 0)), 2)
        expenses_in = round(float(shift_data.get('expenses_in', 0)), 2)
        expenses_out = round(float(shift_data.get('expenses_out', 0)), 2)
        expenses_balance = round(float(shift_data.get('expenses_balance', 0)), 2)

        # Наличные по ККТ = Выручка общая - Безнал - Терминал
        cash_revenue = round(revenue - acquiring_kkt - terminal_actual, 2)
        
        # ДОЛЖНО БЫТЬ = Утро + Наличные по ККТ + Баланс операций
        # Баланс = Внесла (+) - Отдала/Взяла (-)
        expected = round(morning_cash + cash_revenue + expenses_balance, 2)
        actual = round(float(evening_cash), 2)

        # Формируем строку операций
        expenses_str = ""
        if expenses_in > 0:
            expenses_str += f"  • Внесла в кассу: +{expenses_in} руб.\n"
        if expenses_out > 0:
            expenses_str += f"  • Отдала/Взяла: -{expenses_out} руб.\n"
        if expenses_balance != 0:
            expenses_str += f"  • Баланс: {expenses_balance:+.2f} руб.\n"
        else:
            expenses_str = f"  • Нет операций\n"

        msg = (
            f"🔔 ЗАКРЫТИЕ СМЕНЫ\n"
            f"{'━' * 30}\n"
            f"👤 Сотрудник: {user_name}\n"
            f"📅 Дата: {shift_data.get('day', 0)}.{shift_data.get('month', 0)}.{shift_data.get('year', 0)}\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M')}\n"
            f"{'━' * 30}\n"
            f"📊 ИТОГИ СМЕНЫ:\n\n"
            f"📦 Утро: {morning_cash:.2f} руб.\n"
            f"💰 Выручка (ККТ): {revenue:.2f} руб.\n"
            f"  • Наличные: {cash_revenue:.2f} руб.\n"
            f"  • Безнал: {acquiring_kkt:.2f} руб.\n"
            f"💳 Терминал: {terminal_actual:.2f} руб.\n"
            f"💸 Операции:\n{expenses_str}"
            f"{'━' * 30}\n"
            f"📊 Должно быть: {expected:.2f} руб.\n"
            f"💵 Фактически: {actual:.2f} руб.\n"
        )

        if abs(discrepancy) > 0.01:
            if discrepancy > 0:
                msg += f"✅ ИЗЛИШЕК: +{discrepancy:.2f} руб.\n"
            else:
                msg += f"❌ НЕДОСТАЧА: {discrepancy:.2f} руб.\n"
        else:
            msg += f"✅ ВСЁ СХОДИТСЯ: 0.00 руб.\n"

        msg += f"{'━' * 30}\n"
        msg += f"✅ Смена закрыта. Хорошего отдыха!"

    # Отправляем сообщение
    try:
        result = send_message(user_id=int(admin_vk_id), message=msg)
        if result:
            print(f"[VK] Shift notification sent: {shift_action} by {user_name}")
            return True
        else:
            print(f"[VK] Shift notification failed: {shift_action}")
            return False
    except Exception as e:
        print(f"[VK] Shift notification error: {e}")
        return False


if __name__ == "__main__":
    # Тестовый запуск
    print("VK Bot для GrafikRaboty")
    print("=" * 50)
    
    config = load_vk_config()
    if config.get("service_token"):
        print("✓ VK токен настроен")
        print(f"✓ Group ID: {config.get('group_id')}")
        print(f"✓ Admin VK ID: {config.get('admin_vk_id')}")
        
        # Запускаем polling
        start_polling()
        
        # Держим программу запущенной
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_polling()
            print("\nVK Bot остановлен")
    else:
        print("✗ VK токен не настроен")
        print("Отредактируйте vk_config.json")
