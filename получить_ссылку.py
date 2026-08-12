# -*- coding: utf-8 -*-
"""Показывает ссылки для доступа: в локальной сети и из интернета (автоматически на любом компе)."""
import socket
import urllib.request

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_public_ip():
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip", "http://icanhazip.com"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                ip = (r.read().decode() or "").strip()
                if ip and len(ip) < 20:
                    return ip
        except Exception:
            continue
    return None

def main():
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    link_local = f"http://{local_ip}:8080"
    link_public = f"http://{public_ip}:8080" if public_ip else None

    print()
    print("=" * 56)
    print("  ССЫЛКИ ДЛЯ ДОСТУПА (скопируйте и скиньте сотрудницам)")
    print("=" * 56)
    print()
    print("  В той же Wi‑Fi / офисе:")
    print(f"    {link_local}")
    print()
    if link_public:
        print("  Удалённо из интернета (если настроен проброс порта 8080):")
        print(f"    {link_public}")
        print()
    else:
        print("  Удалённо: внешний IP не определён.")
        print("  См. ВНЕШНИЙ_ДОСТУП.txt (проброс порта или туннель).")
        print()
    print("=" * 56)
    print()
    print("  Сначала на этом компе запустите ЗАПУСК.bat.")
    print()
    input("  Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
