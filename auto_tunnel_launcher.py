# -*- coding: utf-8 -*-
"""
Auto Tunnel Launcher - Автоматический запуск туннеля с VK уведомлениями
Запускается вместе с сервером, отправляет уведомления в VK
"""
import sys
import os
import time
import json
import threading
import subprocess
import re
import socket
import urllib.request
import ssl

# SSL контекст
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR
try:
    from app_paths import DATA_DIR
except ImportError:
    pass

TUNNEL_INFO_PATH = os.path.join(DATA_DIR, 'tunnel_info.json')
VK_CONFIG_PATH = os.path.join(DATA_DIR, 'vk_config.json')

# Глобальные переменные
_tunnel_process = None
_tunnel_url = None
_tunnel_password = None


def log_message(message, level="INFO"):
    """Логирование сообщений"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    # Пишем в лог
    try:
        logs_dir = os.path.join(DATA_DIR, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        with open(os.path.join(logs_dir, 'auto_tunnel.log'), 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except:
        pass


def get_local_ip():
    """Получить локальный IP адрес"""
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


def load_vk_config():
    """Загрузить VK конфигурацию"""
    try:
        with open(VK_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def send_vk_message(peer_id, message):
    """Отправить сообщение в VK"""
    config = load_vk_config()
    token = config.get('service_token')
    
    if not token or not peer_id:
        log_message(f"VK message not sent: token={bool(token)}, peer_id={peer_id}", "WARNING")
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


def send_tunnel_notification(tunnel_url, password, local_ip, public_ip):
    """Отправить уведомление о туннеле в VK"""
    config = load_vk_config()
    admin_vk_id = config.get('admin_vk_id')
    chat_peer_id = config.get('chat_peer_id')
    
    msg = (
        "🚀 СЕРВЕР ЗАПУЩЕН — ТУННЕЛЬ АКТИВЕН\n\n"
        "🌐 Туннель (доступ из интернета):\n"
        f"`{tunnel_url}`\n\n"
        "🔐 Пароль для туннеля:\n"
        f"`{password}`\n\n"
        "📍 Локальная сеть (Wi-Fi):\n"
        f"`http://{local_ip}:8080`\n\n"
        "🌍 Внешний IP (проброс портов):\n"
        f"`http://{public_ip}:8080`\n\n"
        "📱 Сотрудникам:\n"
        f"• В той же сети: http://{local_ip}:8080\n"
        f"• Из интернета: {tunnel_url}\n\n"
        f"Время: {time.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        "✅ Все системы работают!"
    )
    
    # Отправляем админу
    if admin_vk_id:
        send_vk_message(int(admin_vk_id), msg)
    
    # Отправляем в чат (если есть)
    if chat_peer_id:
        send_vk_message(int(chat_peer_id), msg)


def find_node():
    """Найти Node.js и вернуть путь к директории с npm"""
    # Сначала ищем где установлен lt глобально
    appdata_npm = os.path.join(os.getenv('APPDATA', ''), 'npm')
    if os.path.exists(os.path.join(appdata_npm, 'lt.cmd')):
        log_message(f"Found lt in AppData: {appdata_npm}")
        return appdata_npm
    
    # Стандартные пути Node.js
    paths = [
        r"C:\Program Files\nodejs",
        r"C:\Program Files (x86)\nodejs",
        os.path.join(os.getenv('APPDATA', ''), '..', 'Local\\Programs\\nodejs')
    ]
    
    for path in paths:
        if os.path.exists(path):
            log_message(f"Found Node.js: {path}")
            return path
    
    # Пробуем найти через where
    try:
        result = subprocess.run(['where', 'node'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            node_path = result.stdout.strip().split('\n')[0]
            node_dir = os.path.dirname(node_path)
            log_message(f"Found Node.js via where: {node_dir}")
            return node_dir
    except:
        pass
    
    return None


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


def save_tunnel_info(tunnel_url, password):
    """Сохранить информацию о туннеле"""
    try:
        local_ip = get_local_ip()
        public_ip = get_public_ip() or local_ip
        
        tunnel_info = {
            'tunnel_url': tunnel_url,
            'password': password,
            'local_ip': local_ip,
            'public_ip': public_ip,
            'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        with open(TUNNEL_INFO_PATH, 'w', encoding='utf-8') as f:
            json.dump(tunnel_info, f, ensure_ascii=False, indent=2)
        
        log_message(f"Tunnel info saved to {TUNNEL_INFO_PATH}")
        return True
    except Exception as e:
        log_message(f"Failed to save tunnel info: {e}", "ERROR")
        return False


def check_tunnel_health(tunnel_url):
    """Проверка здоровья туннеля"""
    if not tunnel_url:
        return False, "No URL"
    
    try:
        req = urllib.request.Request(f"{tunnel_url}/login", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as resp:
            if resp.status in (200, 302):
                return True, "OK"
            else:
                return False, f"Status {resp.status}"
    except Exception as e:
        return False, str(e)


def run_tunnel():
    """Запустить туннель и отправить уведомление"""
    global _tunnel_process, _tunnel_url, _tunnel_password
    
    log_message("=" * 60)
    log_message("AUTO TUNNEL LAUNCHER STARTED")
    log_message("=" * 60)
    
    # Проверяем, запущен ли сервер
    log_message("Checking local server on port 8080...")
    server_ready = False
    
    for i in range(30):  # Ждём до 30 секунд
        time.sleep(1)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 8080))
            sock.close()
            if result == 0:
                server_ready = True
                log_message("✅ Local server is running")
                break
        except:
            pass
    
    if not server_ready:
        log_message("Local server not running! Tunnel cannot start.", "ERROR")
        return
    
    # Находим Node.js / npm
    node_dir = find_node()
    if not node_dir:
        log_message("Node.js not found! Install Node.js for tunnel.", "ERROR")
        return
    
    log_message(f"Node.js/npm found: {node_dir}")
    
    # Запускаем туннель
    lt_path = os.path.join(node_dir, 'lt.cmd')
    
    # Если lt.cmd не найден, пробуем просто 'lt' (через PATH)
    if not os.path.exists(lt_path):
        lt_path = 'lt'
        log_message("Using lt from PATH", "WARNING")
    
    lt_cmd = [lt_path, '-p', '8080']
    
    log_message(f"Starting tunnel: {' '.join(lt_cmd)}")
    
    try:
        _tunnel_process = subprocess.Popen(
            lt_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=node_dir
        )
        log_message(f"Tunnel process started with PID {_tunnel_process.pid}")
    except Exception as e:
        log_message(f"Failed to start tunnel: {e}", "ERROR")
        return
    
    # Читаем вывод туннеля
    tunnel_found = False
    
    while True:
        line = _tunnel_process.stdout.readline()
        if not line:
            break
        
        line = line.strip()
        if line:
            log_message(f"Tunnel: {line}")
            
            # Извлекаем URL
            url = extract_tunnel_url(line)
            if url and not tunnel_found:
                _tunnel_url = url
                _tunnel_password = get_public_ip() or get_local_ip()
                tunnel_found = True
                
                log_message(f"✅ Tunnel URL detected: {url}", "SUCCESS")
                
                # Сохраняем информацию
                save_tunnel_info(_tunnel_url, _tunnel_password)
                
                # Отправляем уведомление
                local_ip = get_local_ip()
                public_ip = get_public_ip() or local_ip
                
                send_tunnel_notification(
                    _tunnel_url,
                    _tunnel_password,
                    local_ip,
                    public_ip
                )
                
                log_message("VK notification sent", "SUCCESS")
                break
    
    # Мониторинг туннеля
    if tunnel_found:
        log_message("Tunnel monitoring started...")
        
        while True:
            time.sleep(60)  # Проверяем каждую минуту
            
            # Проверяем процесс
            if _tunnel_process.poll() is not None:
                log_message("Tunnel process died! Restarting...", "WARNING")
                time.sleep(5)
                run_tunnel()  # Перезапускаем
                break
            
            # Проверяем здоровье
            if _tunnel_url:
                healthy, status = check_tunnel_health(_tunnel_url)
                if not healthy:
                    log_message(f"Tunnel health check failed: {status}", "WARNING")
                else:
                    log_message(f"Tunnel health: OK", "SUCCESS")


def start_auto_tunnel():
    """Запустить автозапуск туннеля в отдельном потоке"""
    tunnel_thread = threading.Thread(target=run_tunnel, daemon=True)
    tunnel_thread.start()
    log_message("Auto tunnel launcher started in background thread")
    return tunnel_thread


if __name__ == '__main__':
    import socket
    try:
        run_tunnel()
    except KeyboardInterrupt:
        log_message("Stopped by user")
    except Exception as e:
        log_message(f"Fatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
