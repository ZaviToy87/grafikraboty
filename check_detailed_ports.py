# -*- coding: utf-8 -*-
"""
Детальная проверка проброса портов
"""
import socket
import urllib.request
import ssl
import json
import os

_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_public_ip():
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


def check_port(host, port, timeout=5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def check_server_response(base_url):
    """Проверяем, что отвечает сервер"""
    try:
        req = urllib.request.Request(f"{base_url}/login", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5, context=_ssl_context) as r:
            content = r.read().decode('utf-8', errors='ignore')
            return r.status, len(content), 'GrafikRaboty' in content or 'login' in content.lower()
    except Exception as e:
        return None, 0, str(e)


def main():
    print("=" * 70)
    print(" ДЕТАЛЬНАЯ ПРОВЕРКА ПРОБРОСА ПОРТОВ")
    print("=" * 70)
    print()

    local_ip = get_local_ip()
    public_ip = get_public_ip() or "Не определён"

    print(f"📍 Локальный IP: {local_ip}")
    print(f"🌍 Внешний IP: {public_ip}")
    print()

    # Проверяем локальный сервер
    print("1️⃣ ПРОВЕРКА ЛОКАЛЬНОГО СЕРВЕРА (127.0.0.1):")
    print("-" * 50)
    for port in [8080, 5000, 80]:
        status = check_port('127.0.0.1', port)
        if status:
            code, size, is_ours = check_server_response(f"http://127.0.0.1:{port}")
            marker = "✅ НАШ СЕРВЕР" if is_ours else "⚠️ ЧУЖОЙ СЕРВЕР"
            print(f"  Порт {port}: {marker} (статус: {code})")
        else:
            print(f"  Порт {port}: ❌ Закрыт")
    print()

    # Проверяем по локальной сети
    print("2️⃣ ПРОВЕРКА ПО ЛОКАЛЬНОЙ СЕТИ (%s):" % local_ip)
    print("-" * 50)
    for port in [8080, 5000, 80]:
        status = check_port(local_ip, port, timeout=5)
        if status:
            code, size, is_ours = check_server_response(f"http://{local_ip}:{port}")
            marker = "✅ НАШ СЕРВЕР" if is_ours else "⚠️ ЧУЖОЙ СЕРВЕР"
            print(f"  Порт {port}: {marker} (статус: {code})")
        else:
            print(f"  Порт {port}: ❌ Закрыт")
    print()

    # Проверяем по внешнему IP
    print("3️⃣ ПРОВЕРКА ПО ВНЕШНЕМУ IP (%s):" % public_ip)
    print("-" * 50)
    for port in [8080, 5000, 80]:
        status = check_port(public_ip, port, timeout=10)
        if status:
            code, size, is_ours = check_server_response(f"http://{public_ip}:{port}")
            if is_ours:
                print(f"  Порт {port}: ✅ НАШ СЕРВЕР (проброшен правильно)")
            else:
                print(f"  Порт {port}: ⚠️ ОТВЕЧАЕТ РОУТЕР/ДРУГОЙ СЕРВЕР (статус: {code})")
        else:
            print(f"  Порт {port}: ❌ Закрыт")
    print()

    # Рекомендации
    print("=" * 70)
    print(" РЕКОМЕНДАЦИИ:")
    print("=" * 70)
    print()
    
    # Проверяем проблему
    local_8080 = check_port('127.0.0.1', 8080)
    _, _, local_is_ours = check_server_response("http://127.0.0.1:8080")
    
    wan_8080 = check_port(public_ip, 8080) if public_ip != "Не определён" else False
    wan_is_ours = False
    if wan_8080:
        _, _, wan_is_ours = check_server_response(f"http://{public_ip}:8080")
    
    if local_is_ours and wan_8080 and not wan_is_ours:
        print("❌ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
        print()
        print("На порту 8080 локально — твой сервер GrafikRaboty")
        print("На порту 8080 внешне — отвечает РОУТЕР (страница входа роутера)")
        print()
        print("📝 РЕШЕНИЕ:")
        print()
        print("1. Зайди в настройки роутера (обычно http://192.168.1.1)")
        print("2. Найди раздел 'Port Forwarding' / 'Виртуальные серверы' / 'NAT'")
        print("3. Удали или измени правило для порта 8080")
        print("4. Создай ПРАВИЛЬНЫЙ проброс:")
        print()
        print("   ┌─────────────────────────────────────────────┐")
        print("   │ Настройка проброса порта                    │")
        print("   ├─────────────────────────────────────────────┤")
        print("   │ Внешний порт (WAN):  8080                   │")
        print("   │ Внутренний порт (LAN): 8080                 │")
        print("   │ Внутренний IP: %s          │" % local_ip.ljust(18) + "│")
        print("   │ Протокол: TCP (или TCP/UDP)                 │")
        print("   │ Статус: Включено                            │")
        print("   └─────────────────────────────────────────────┘")
        print()
        print("5. Сохрани и перезагрузи роутер")
        print("6. Запусти эту проверку снова")
        print()
        print("📍 Альтернатива: Используй порт 5000 для сервера")
        print("   Если на 8080 отвечает роутер, можно перенастроить")
        print("   сервер на порт 5000 (если он свободен)")
    elif local_is_ours and wan_is_ours:
        print("✅ ВСЁ РАБОТАЕТ ПРАВИЛЬНО!")
        print()
        print("Внешний доступ к серверу GrafikRaboty настроен корректно")
    else:
        print("⚠️ СЕРВЕР НЕ ЗАПУЩЕН ИЛИ НЕДОСТУПЕН")
        print()
        print("Проверь, запущен ли сервер на порту 8080")
    
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
