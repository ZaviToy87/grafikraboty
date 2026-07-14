# -*- coding: utf-8 -*-
"""
Модуль уведомлений: Telegram + VK.
Отправляет оповещения при запуске сервера, открытии/закрытии смены и т.д.
"""

import os
import json
import time
import urllib.request
import urllib.error
import ssl
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Константы
VK_API_VERSION = "5.199"
VK_API_URL = "https://api.vk.com/method/"


def _load_telegram_config():
    """Загружает конфиг Telegram из telegram_config.json"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram_config.json")
    if not os.path.exists(config_path):
        logger.warning(f"telegram_config.json не найден: {config_path}")
        return None, None
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        bot_token = cfg.get("bot_token", "").strip()
        chat_ids = cfg.get("chat_ids", [])
        if isinstance(chat_ids, str):
            chat_ids = [chat_ids]
        return bot_token, chat_ids
    except Exception as e:
        logger.error(f"Ошибка загрузки telegram_config.json: {e}")
        return None, None


def send_telegram(text):
    """Отправляет сообщение в Telegram"""
    bot_token, chat_ids = _load_telegram_config()
    if not bot_token or not chat_ids:
        logger.warning("Telegram не настроен (bot_token или chat_ids пусты)")
        return False
    
    success = False
    for chat_id in chat_ids:
        chat_id = str(chat_id).strip()
        if not chat_id:
            continue
        
        for attempt in range(3):
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = urllib.parse.urlencode({
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=data)
                with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    if result.get("ok"):
                        success = True
                        break
                    else:
                        logger.warning(f"Telegram API error: {result}")
            except Exception as e:
                logger.warning(f"Telegram attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)
    
    return success


def send_vk_message(message, keyboard=None):
    """Отправляет сообщение админу через VK"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vk_config.json")
    if not os.path.exists(config_path):
        logger.warning("vk_config.json не найден")
        return False
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        token = cfg.get("group_token", "") or cfg.get("access_token", "")
        admin_id = cfg.get("admin_id", "") or cfg.get("owner_id", "")
        
        if not token or not admin_id:
            logger.warning("VK не настроен (token или admin_id пусты)")
            return False
        
        # Отправляем сообщение
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        params = {
            "access_token": token,
            "v": VK_API_VERSION,
            "peer_id": admin_id,
            "message": message,
            "random_id": int(time.time() * 1000)
        }
        
        if keyboard:
            params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
        
        url = VK_API_URL + "messages.send"
        data = urllib.parse.urlencode(params).encode("utf-8")
        
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "error" in result:
                logger.error(f"VK API error: {result['error']}")
                return False
            return True
            
    except Exception as e:
        logger.error(f"Ошибка отправки VK: {e}")
        return False


def notify_server_start(link_local, public_ip=None, tunnel_url=None):
    """Уведомление о запуске сервера"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    msg = (
        f"\U0001f4e1 Сервер графика работы запущен.\n\n"
        f"\U0001f4c5 {now}\n\n"
        f"\U0001f4bb Локально:\nhttp://127.0.0.1:8080\n\n"
    )
    
    if link_local:
        msg += f"\U0001f3e0 В сети:\n{link_local}\n\n"
    
    if tunnel_url:
        msg += f"\U0001f310 Через туннель:\n{tunnel_url}\n\n"
    
    if public_ip:
        msg += f"\U0001f30d Внешний IP: {public_ip}\n\n"
    
    msg += (
        f"\U0001f511 Пароль при запросе: pass123\n\n"
        f"\U0001f4a1 Для остановки нажмите Ctrl+C в окне сервера"
    )
    
    # Отправляем в Telegram
    send_telegram(msg)
    
    # Отправляем в VK
    vk_msg = (
        f"\U0001f4e1 Сервер графика работы запущен!\n"
        f"\U0001f4c5 {now}\n\n"
        f"\U0001f4bb http://127.0.0.1:8080"
    )
    if tunnel_url:
        vk_msg += f"\n\U0001f310 {tunnel_url}"
    send_vk_message(vk_msg)


def notify_shift_opened(employee_name, shift_type):
    """Уведомление об открытии смены"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    msg = (
        f"\U0001f534 СМЕНА ОТКРЫТА\n"
        f"\U0001f464 Сотрудник: {employee_name}\n"
        f"\U0001f4c5 {now}\n"
        f"\U0001f3e0 Тип: {shift_type}"
    )
    
    send_telegram(msg)
    send_vk_message(msg)


def notify_shift_closed(employee_name, shift_type, duration):
    """Уведомление о закрытии смены"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    msg = (
        f"\U0001f7e2 СМЕНА ЗАКРЫТА\n"
        f"\U0001f464 Сотрудник: {employee_name}\n"
        f"\U0001f4c5 {now}\n"
        f"\U0001f3e0 Тип: {shift_type}\n"
        f"\U000023f0 Длительность: {duration}"
    )
    
    send_telegram(msg)
    send_vk_message(msg)


def notify_error(error_text):
    """Уведомление об ошибке"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    msg = (
        f"\u274c ОШИБКА\n"
        f"\U0001f4c5 {now}\n"
        f"{error_text}"
    )
    
    send_telegram(msg)
    send_vk_message(msg)


def send_vk_code(code, employee_name):
    """Отправляет код для входа в VK админу"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    msg = (
        f"\U0001f511 КОД ДЛЯ ВХОДА В VK\n"
        f"\U0001f464 Сотрудник: {employee_name}\n"
        f"\U0001f4c5 {now}\n\n"
        f"\U0001f511 Код: {code}"
    )
    
    send_telegram(msg)
    send_vk_message(msg)


if __name__ == "__main__":
    # Тест
    logging.basicConfig(level=logging.INFO)
    print("Тест уведомлений...")
    notify_server_start("http://192.168.1.100:8080", "1.2.3.4", "https://tunnel.example.com")
    print("Готово!")
