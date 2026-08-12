# -*- coding: utf-8 -*-
"""
Tunnel Manager v2.0
- Мониторинг туннеля с логированием подключений
- Проверка доступности туннеля
- Актуальные уведомления с правильными IP
- Автоматический рестарт при проблемах
"""
import os
import sys
import json
import time
import socket
import urllib.request
import ssl
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Пути
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR
LOGS_DIR = SCRIPT_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

TUNNEL_INFO_PATH = DATA_DIR / 'tunnel_info.json'
TUNNEL_LOG_PATH = LOGS_DIR / 'tunnel_connections.log'
VK_CONFIG_PATH = DATA_DIR / 'vk_config.json'

# Настройки
TUNNEL_PORT = 8080
NODE_CHECK_TIMEOUT = 5
TUNNEL_CHECK_INTERVAL = 30
MAX_RESTARTS = 5

# SSL контекст
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def log_message(message, level="INFO"):
    """Логирование сообщений"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    # Пишем в лог
    try:
        with open(LOGS_DIR / 'tunnel_monitor.log', 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except:
        pass


def get_local_ip():
    """Получить локальный IP адрес в сети"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_public_ip():
    """Получить внешний IP адрес"""
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8, context=_ssl_context) as r:
                ip = r.read().decode().strip()
                if ip and len(ip) < 20:
                    return ip
        except:
            continue
    return None


def check_port(host, port):
    """Проверка доступности порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def find_node():
    """Найти Node.js"""
    paths = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.join(os.getenv('APPDATA', ''), '..', 'Local\\Programs\\nodejs\\node.exe')
    ]
    
    for path in paths:
        if os.path.exists(path):
            return os.path.dirname(path)
    
    # Пробуем найти через where
    try:
        result = subprocess.run(['where', 'node'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            node_path = result.stdout.strip().split('\n')[0]
            return os.path.dirname(node_path)
    except:
        pass
    
    return None


def load_vk_config():
    """Загрузить VK конфиг"""
    try:
        with open(VK_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'admin_vk_id': None, 'chat_peer_id': None}


def send_vk_message(peer_id, message):
    """Отправить сообщение в VK"""
    config = load_vk_config()
    token = config.get('service_token')
    
    if not token or not peer_id:
        return False
    
    try:
        url = f"https://api.vk.com/method/messages.send?peer_id={peer_id}&message={urllib.parse.quote(message)}&random_id={int(time.time() * 1000)}&access_token={token}&v=5.131"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if 'response' in result:
                log_message(f"VK message sent to {peer_id}")
                return True
            else:
                log_message(f"VK error: {result}", "ERROR")
                return False
    except Exception as e:
        log_message(f"VK send error: {e}", "ERROR")
        return False


def send_tunnel_notification(tunnel_url, password, local_ip, public_ip, is_restart=False, restart_count=0):
    """Отправить уведомление о туннеле"""
    config = load_vk_config()
    admin_vk_id = config.get('admin_vk_id')
    chat_peer_id = config.get('chat_peer_id')
    
    if is_restart:
        msg = (
            f"⚠️ *ТУННЕЛЬ ПЕРЕЗАПУЩЕН*\n\n"
            f"Попытка: {restart_count}\n\n"
            f"🌐 *Ссылка на туннель:*\n"
            f"`{tunnel_url}`\n\n"
            f"🔐 *Пароль:*\n"
            f"`{password}`\n\n"
            f"📍 *Локальная сеть:*\n"
            f"`http://{local_ip}:8080`\n\n"
            f"🌍 *Внешний IP:*\n"
            f"`http://{public_ip}:8080`\n\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"Если не работает:\n"
            f"1. Проверьте интернет\n"
            f"2. Используйте локальную ссылку\n"
            f"3. Перезапустите сервер"
        )
    else:
        msg = (
            f"✅ *СЕРВЕР ЗАПУЩЕН*\n\n"
            f"🌐 *Туннель (доступ из интернета):*\n"
            f"`{tunnel_url}`\n\n"
            f"🔐 *Пароль для туннеля:*\n"
            f"`{password}`\n\n"
            f"📍 *Локальная сеть (Wi-Fi):*\n"
            f"`http://{local_ip}:8080`\n\n"
            f"🌍 *Внешний IP (проброс портов):*\n"
            f"`http://{public_ip}:8080`\n\n"
            f"📱 *Ссылки для сотрудников:*\n"
            f"• В той же сети: http://{local_ip}:8080\n"
            f"• Из интернета: {tunnel_url}\n\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"✅ Все системы работают!"
        )
    
    # Отправляем админу
    if admin_vk_id:
        send_vk_message(int(admin_vk_id), msg)
    
    # Отправляем в чат (если есть)
    if chat_peer_id:
        send_vk_message(int(chat_peer_id), msg)


def send_tunnel_error(error_message, restart_count):
    """Отправить уведомление об ошибке"""
    config = load_vk_config()
    admin_vk_id = config.get('admin_vk_id')
    
    if not admin_vk_id:
        return
    
    msg = (
        f"❌ *ОШИБКА ТУННЕЛЯ!*\n\n"
        f"Превышен лимит перезапусков ({restart_count}).\n\n"
        f"Ошибка: {error_message}\n\n"
        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"Требуется вмешательство:\n"
        f"1. Проверьте интернет\n"
        f"2. Проверьте, запущен ли сервер\n"
        f"3. Перезапустите вручную"
    )
    
    send_vk_message(int(admin_vk_id), msg)


def log_tunnel_connection(url, status="connected"):
    """Логирование подключения к туннелю"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {status} - {url}\n"
        
        with open(TUNNEL_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        log_message(f"Connection logged: {status} - {url}")
    except Exception as e:
        log_message(f"Failed to log connection: {e}", "ERROR")


def check_tunnel_health(tunnel_url):
    """Проверка здоровья туннеля"""
    if not tunnel_url:
        return False, "No URL"
    
    try:
        # Пробуем подключиться к туннелю
        req = urllib.request.Request(tunnel_url + '/api/health', headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as resp:
            if resp.status == 200:
                return True, "OK"
            else:
                return False, f"Status {resp.status}"
    except Exception as e:
        return False, str(e)


def extract_tunnel_url(line):
    """Извлечь URL туннеля из лога"""
    patterns = [
        r"https://[a-zA-Z0-9\-]+\.loca\.lt",
        r"https://[a-zA-Z0-9\-]+\.localtunnel\.me",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            url = match.group(0).rstrip(").\"' \t\n")
            if url.startswith("https://"):
                return url
    return None


def start_tunnel(node_dir, port):
    """Запустить туннель"""
    lt_path = os.path.join(node_dir, 'lt')
    lt_cmd = [lt_path, '-p', str(port)]
    
    try:
        process = subprocess.Popen(
            lt_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=node_dir
        )
        log_message(f"Tunnel process started with PID {process.pid}")
        return process
    except Exception as e:
        log_message(f"Failed to start tunnel: {e}", "ERROR")
        return None


def monitor_tunnel():
    """Мониторинг туннеля"""
    log_message("="*60)
    log_message("TUNNEL MANAGER v2.0 STARTED")
    log_message("="*60)
    
    # Проверка Node.js
    node_dir = find_node()
    if not node_dir:
        log_message("Node.js not found!", "ERROR")
        return
    
    log_message(f"Node.js found: {node_dir}")
    
    # Проверка локального сервера
    log_message(f"Checking local server on port {TUNNEL_PORT}...")
    if not check_port('127.0.0.1', TUNNEL_PORT):
        log_message(f"Local server not running on port {TUNNEL_PORT}!", "ERROR")
        log_message("Waiting 30 seconds before retry...", "WARNING")
        time.sleep(30)
        if not check_port('127.0.0.1', TUNNEL_PORT):
            log_message("Local server still not running. Exiting.", "ERROR")
            return
    
    log_message("✅ Local server is running")
    
    # Получаем IP
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    log_message(f"Local IP: {local_ip}")
    log_message(f"Public IP: {public_ip}")
    
    # Запускаем туннель
    restart_count = 0
    tunnel_process = start_tunnel(node_dir, TUNNEL_PORT)
    
    if not tunnel_process:
        log_message("Failed to start tunnel process", "ERROR")
        return
    
    current_tunnel_url = None
    last_check_time = time.time()
    
    # Читаем вывод туннеля
    while True:
        line = tunnel_process.stdout.readline()
        if not line:
            break
        
        line = line.strip()
        if line:
            log_message(f"Tunnel: {line}")
            
            # Извлекаем URL
            url = extract_tunnel_url(line)
            if url and url != current_tunnel_url:
                current_tunnel_url = url
                log_message(f"✅ New tunnel URL detected: {url}", "SUCCESS")
                
                # Сохраняем информацию
                tunnel_info = {
                    'tunnel_url': url,
                    'password': public_ip or local_ip,
                    'local_ip': local_ip,
                    'public_ip': public_ip,
                    'started_at': datetime.now().isoformat(),
                    'restart_count': restart_count
                }
                
                try:
                    with open(TUNNEL_INFO_PATH, 'w', encoding='utf-8') as f:
                        json.dump(tunnel_info, f, ensure_ascii=False, indent=2)
                    log_message(f"Tunnel info saved to {TUNNEL_INFO_PATH}")
                except Exception as e:
                    log_message(f"Failed to save tunnel info: {e}", "ERROR")
                
                # Отправляем уведомление
                password = public_ip or local_ip
                send_tunnel_notification(
                    url, 
                    password, 
                    local_ip, 
                    public_ip,
                    is_restart=(restart_count > 0),
                    restart_count=restart_count
                )
                
                # Логируем подключение
                log_tunnel_connection(url, "tunnel_started")
        
        # Периодическая проверка здоровья
        current_time = time.time()
        if current_time - last_check_time > TUNNEL_CHECK_INTERVAL:
            last_check_time = current_time
            
            if current_tunnel_url:
                healthy, status = check_tunnel_health(current_tunnel_url)
                if not healthy:
                    log_message(f"Tunnel health check failed: {status}", "WARNING")
                    restart_count += 1
                    
                    if restart_count >= MAX_RESTARTS:
                        log_message("Max restarts reached. Sending error notification.", "ERROR")
                        send_tunnel_error(status, restart_count)
                        break
                    
                    # Перезапускаем туннель
                    log_message(f"Restarting tunnel (attempt {restart_count}/{MAX_RESTARTS})...", "WARNING")
                    tunnel_process.terminate()
                    time.sleep(5)
                    tunnel_process = start_tunnel(node_dir, TUNNEL_PORT)
                else:
                    log_message(f"Tunnel health check: OK", "SUCCESS")
    
    log_message("Tunnel monitor stopped")


if __name__ == '__main__':
    try:
        monitor_tunnel()
    except KeyboardInterrupt:
        log_message("Stopped by user")
    except Exception as e:
        log_message(f"Fatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
