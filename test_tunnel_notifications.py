# -*- coding: utf-8 -*-
"""
Тест уведомлений туннеля
Проверка, какие сообщения приходят
"""
import sys
sys.path.insert(0, '.')

from vk_bot import get_local_ip, get_public_ip, load_vk_config

def main():
    print("="*60)
    print("🔍 ТЕСТ УВЕДОМЛЕНИЙ ТУННЕЛЯ")
    print("="*60)
    
    # Получаем IP
    print("\n📍 IP-АДРЕСА:")
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    print(f"  Локальный IP: {local_ip}")
    print(f"  Внешний IP:   {public_ip}")
    
    # Загружаем конфиг
    print("\n📱 VK КОНФИГ:")
    config = load_vk_config()
    admin_vk_id = config.get('admin_vk_id')
    chat_peer_id = config.get('chat_peer_id')
    tunnel_url = "https://test-tunnel.loca.lt"
    password = public_ip or local_ip
    
    print(f"  Admin VK ID: {admin_vk_id}")
    print(f"  Chat Peer ID: {chat_peer_id}")
    
    # Формируем сообщение v2.0
    print("\n📝 СООБЩЕНИЕ v2.0, КОТОРОЕ ПРИДЁТ:")
    print("-"*60)
    
    msg = (
        f"🚀 СЕРВЕР ЗАПУЩЕН — ВЕРСИЯ 2.0 🚀\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 ТУННЕЛЬ (интернет):\n"
        f"`{tunnel_url}`\n"
        f"🔐 Пароль: `{password}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"📍 ЛОКАЛЬНАЯ СЕТЬ (Wi-Fi):\n"
        f"👉 `http://{local_ip}:8080`\n\n"
        
        f"🌍 ВНЕШНИЙ IP (проброс):\n"
        f"👉 `http://{public_ip}:8080`\n\n"
        
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 СОТРУДНИКАМ:\n"
        f"• Дома (Wi-Fi): http://{local_ip}:8080\n"
        f"• Извне: {tunnel_url}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"⏰ {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"✅ v2.0 — Все IP актуальны!"
    )
    
    print(msg)
    print("-"*60)
    
    # Проверка
    print("\n✅ ПРОВЕРКА:")
    if "127.0.0.1" in msg:
        print("  ❌ ЕСТЬ 127.0.0.1 — это плохо!")
    else:
        print("  ✅ Нет 127.0.0.1 — хорошо!")
    
    if local_ip in msg:
        print(f"  ✅ Локальный IP ({local_ip}) присутствует")
    
    if public_ip in msg:
        print(f"  ✅ Внешний IP ({public_ip}) присутствует")
    
    if tunnel_url in msg:
        print(f"  ✅ Ссылка на туннель присутствует")
    
    print("\n" + "="*60)
    print("💡 Если сообщение выглядит правильно — перезапустите сервер")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
