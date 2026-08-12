# -*- coding: utf-8 -*-
"""
Проверка сетевой конфигурации и проброса портов
"""
import socket
import urllib.request
import ssl
import json
import os

# SSL контекст
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def get_local_ip():
    """Локальный IP в сети"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_public_ip():
    """Внешний IP"""
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


def check_port(host, port, timeout=3):
    """Проверка доступности порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def check_server_health(base_url):
    """Проверка доступности сервера"""
    try:
        req = urllib.request.Request(f"{base_url}/login", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5, context=_ssl_context) as r:
            return r.status == 200
    except:
        return False


def main():
    print("=" * 70)
    print(" ПРОВЕРКА СЕТЕВОЙ КОНФИГУРАЦИИ GRAFIKRABOTY")
    print("=" * 70)
    print()

    # Получаем IP
    local_ip = get_local_ip()
    public_ip = get_public_ip() or "Не определён"

    print(f"📍 Локальный IP: {local_ip}")
    print(f"🌍 Внешний IP: {public_ip}")
    print()

    # Проверяем порты локально
    print("🔍 Проверка локальных портов:")
    port_8080 = check_port('127.0.0.1', 8080)
    port_5000 = check_port('127.0.0.1', 5000)
    
    print(f"  Порт 8080 (веб-сервер): {'✅' if port_8080 else '❌'}")
    print(f"  Порт 5000 (проброшен в роутере): {'✅' if port_5000 else '❌'}")
    print()

    # Проверяем доступность по локальной сети
    print("🔍 Проверка доступа по локальной сети:")
    lan_8080 = check_port(local_ip, 8080, timeout=5)
    print(f"  http://{local_ip}:8080 : {'✅' if lan_8080 else '❌'}")
    print()

    # Проверяем доступность по внешнему IP (требует проброса портов)
    print("🔍 Проверка доступа по внешнему IP (требуется проброс портов):")
    if public_ip != "Не определён":
        wan_8080 = check_port(public_ip, 8080, timeout=10)
        wan_5000 = check_port(public_ip, 5000, timeout=10)
        print(f"  http://{public_ip}:8080 : {'✅' if wan_8080 else '❌'} (проброс 8080→8080)")
        print(f"  http://{public_ip}:5000 : {'✅' if wan_5000 else '❌'} (проброс 5000→5000)")
    else:
        print("  ⚠ Не удалось определить внешний IP")
    print()

    # Проверяем туннель
    print("🔍 Проверка туннеля (loca.lt):")
    tunnel_info_path = os.path.join(os.path.dirname(__file__), 'tunnel_info.json')
    if os.path.exists(tunnel_info_path):
        with open(tunnel_info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        tunnel_url = info.get('tunnel_url', '')
        password = info.get('password', '')
        
        print(f"  URL: {tunnel_url}")
        print(f"  Пароль: {password}")
        
        if tunnel_url:
            tunnel_ok = check_server_health(tunnel_url)
            print(f"  Статус: {'✅ Доступен' if tunnel_ok else '❌ Недоступен'}")
    else:
        print("  ⚠ tunnel_info.json не найден")
    print()

    # Проверяем конфигурацию
    print("📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ:")
    print(f"  ✅ Веб-сервер запущен на порту: 8080")
    print(f"  ⚠️  В роутере проброшен порт: 5000")
    print()

    # Выводим рекомендации
    print("=" * 70)
    print(" РЕКОМЕНДАЦИИ:")
    print("=" * 70)
    print()
    print("❌ ПРОБЛЕМА: Порт сервера (8080) НЕ СОВПАДАЕТ с проброшенным портом (5000)")
    print()
    print("📝 ВАРИАНТЫ РЕШЕНИЯ:")
    print()
    print("  📌 ВАРИАНТ 1 (РЕКОМЕНДУЕТСЯ): Изменить проброс портов в роутере")
    print("     1. Зайдите в настройки роутера (обычно 192.168.1.1)")
    print("     2. Найдите 'Port Forwarding' / 'Виртуальные серверы'")
    print("     3. Измените правило:")
    print(f"        - Внешний порт: 8080")
    print(f"        - Внутренний порт: 8080")
    print(f"        - Внутренний IP: {local_ip}")
    print("     4. Сохраните и перезагрузите роутер")
    print()
    print("  📌 ВАРИАНТ 2: Изменить порт сервера на 5000")
    print("     Требует изменения кода в main_launcher.py и web_server.py")
    print()
    print("📍 ССЫЛКИ ДЛЯ СОТРУДНИКОВ (после настройки):")
    print(f"  • Wi-Fi (локально): http://{local_ip}:8080")
    if public_ip != "Не определён":
        print(f"  • Интернет (внешний IP): http://{public_ip}:8080")
    if tunnel_url:
        print(f"  • Туннель: {tunnel_url} (пароль: {password})")
    print()
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
