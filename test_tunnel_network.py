# -*- coding: utf-8 -*-
"""
Тест туннеля и сети
Проверка всех IP, портов и уведомлений
"""
import socket
import urllib.request
import json
import ssl
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VK_CONFIG_PATH = SCRIPT_DIR / 'vk_config.json'
TUNNEL_INFO_PATH = SCRIPT_DIR / 'tunnel_info.json'

_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def get_local_ip():
    """Получить локальный IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_public_ip():
    """Получить внешний IP"""
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
    """Проверка порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def check_url(url, timeout=10):
    """Проверка доступности URL"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context) as resp:
            return resp.status == 200
    except Exception as e:
        return False


def load_tunnel_info():
    """Загрузить информацию о туннеле"""
    try:
        with open(TUNNEL_INFO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def load_vk_config():
    """Загрузить VK конфиг"""
    try:
        with open(VK_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def main():
    print("="*60)
    print("🔍 ТЕСТ ТУННЕЛЯ И СЕТИ")
    print("="*60)
    
    # 1. Проверка IP
    print("\n📍 IP-АДРЕСА:")
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    print(f"  Локальный IP: {local_ip}")
    print(f"  Внешний IP:   {public_ip or 'Не определён'}")
    
    # 2. Проверка портов
    print("\n🔌 ПРОВЕРКА ПОРТОВ:")
    port_8080 = check_port('127.0.0.1', 8080)
    port_5000 = check_port('127.0.0.1', 5000)
    print(f"  Порт 8080 (веб): {'✅' if port_8080 else '❌'}")
    print(f"  Порт 5000 (socket): {'✅' if port_5000 else '❌'}")
    
    # 3. Проверка локального сервера
    print("\n🌐 ЛОКАЛЬНЫЙ СЕРВЕР:")
    local_url = f"http://{local_ip}:8080"
    local_health = check_url(f"http://127.0.0.1:8080/api/health")
    print(f"  URL: {local_url}")
    print(f"  Health API: {'✅ Работает' if local_health else '❌ Не работает'}")
    
    # 4. Информация о туннеле
    print("\n🌍 ТУННЕЛЬ:")
    tunnel_info = load_tunnel_info()
    if tunnel_info:
        tunnel_url = tunnel_info.get('tunnel_url', 'Неизвестно')
        password = tunnel_info.get('password', 'Неизвестно')
        started_at = tunnel_info.get('started_at', 'Неизвестно')
        restart_count = tunnel_info.get('restart_count', 0)
        
        print(f"  URL: {tunnel_url}")
        print(f"  Пароль: {password}")
        print(f"  Запущен: {started_at}")
        print(f"  Перезапусков: {restart_count}")
        
        # Проверка туннеля
        if tunnel_url:
            tunnel_health = check_url(f"{tunnel_url}/api/health")
            print(f"  Статус: {'✅ Работает' if tunnel_health else '❌ Не работает'}")
    else:
        print("  ❌ Информация о туннеле не найдена")
        print("  Возможно, туннель ещё не запущен")
    
    # 5. VK конфигурация
    print("\n📱 VK КОНФИГУРАЦИЯ:")
    vk_config = load_vk_config()
    if vk_config:
        admin_id = vk_config.get('admin_vk_id')
        chat_peer_id = vk_config.get('chat_peer_id')
        token = vk_config.get('service_token')
        
        print(f"  Admin VK ID: {admin_id or '❌ Не настроен'}")
        print(f"  Chat Peer ID: {chat_peer_id or '❌ Не настроен'}")
        print(f"  Token: {'✅ Настроен' if token else '❌ Не настроен'}")
    else:
        print("  ❌ VK конфиг не найден")
    
    # 6. Ссылки для сотрудников
    print("\n📱 ССЫЛКИ ДЛЯ СОТРУДНИКОВ:")
    print(f"  1. Wi-Fi (локально): {local_url}")
    if tunnel_info and tunnel_info.get('tunnel_url'):
        print(f"  2. Туннель: {tunnel_info['tunnel_url']}")
        print(f"     Пароль: {tunnel_info.get('password', '???')}")
    if public_ip:
        print(f"  3. Интернет (проброс): http://{public_ip}:8080")
    
    # 7. Итог
    print("\n" + "="*60)
    print("📊 ИТОГ:")
    
    issues = []
    
    if not port_8080:
        issues.append("❌ Порт 8080 не работает — перезапустите сервер")
    
    if not local_health:
        issues.append("❌ Health API не работает — проверьте сервер")
    
    if not tunnel_info:
        issues.append("⚠️  Туннель не запущен — запустите tunnel_manager_v2.py")
    elif not check_url(f"{tunnel_info.get('tunnel_url', '')}/api/health"):
        issues.append("⚠️  Туннель не работает — перезапустите")
    
    if not vk_config or not vk_config.get('service_token'):
        issues.append("❌ VK не настроен — проверьте vk_config.json")
    
    if issues:
        print("\n⚠️  ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ ВСЁ РАБОТАЕТ!")
    
    print("\n" + "="*60)
    
    # 8. Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("  1. Для запуска туннеля: python tunnel_manager_v2.py")
    print("  2. Для проверки логов: logs/tunnel_monitor.log")
    print("  3. Для перезапуска: Ctrl+C → запустить заново")
    print("  4. Сотрудникам давать ссылку из раздела 'ССЫЛКИ'")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
