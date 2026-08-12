# -*- coding: utf-8 -*-
"""
Скрипт для добавления VK уведомления в main_launcher.py
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
main_launcher_path = os.path.join(BASE_DIR, 'main_launcher.py')

print(f"Editing: {main_launcher_path}")

with open(main_launcher_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем функцию _send_vk_startup_notification перед _notify_telegram_and_hint
vk_function = '''
def _send_vk_startup_notification(local_ip, link_local, link_public):
    """Отправить VK уведомление о запуске сервера"""
    try:
        import vk_startup
        # Получим URL туннеля из файла
        tunnel_url = "настраивается..."
        tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
        if os.path.exists(tunnel_info_path):
            import json
            with open(tunnel_info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
                tunnel_url = info.get('tunnel_url', tunnel_url)
        
        vk_startup.send_vk_startup_notification(
            tunnel_url=tunnel_url,
            password=link_public or local_ip,
            link_local=link_local,
            local_ip=local_ip
        )
        print("✅ VK уведомление отправлено администратору")
    except Exception as e:
        print(f"⚠️ VK уведомление: {e}")


'''

insert_marker = 'def _notify_telegram_and_hint(local_ip, link_local, link_public):'
if insert_marker in content:
    content = content.replace(insert_marker, vk_function + insert_marker, 1)
    print("✅ Function added")
else:
    print("❌ Could not find insert marker")

# 2. Добавляем вызов функции после _notify_telegram_and_hint
old_call = '_notify_telegram_and_hint(local_ip, link_local, link_public)'
new_call = '''_notify_telegram_and_hint(local_ip, link_local, link_public)

    # VK уведомление администратору
    _send_vk_startup_notification(local_ip, link_local, link_public)'''

if old_call in content:
    content = content.replace(old_call, new_call, 1)
    print("✅ Function call added")
else:
    print("❌ Could not find function call")

with open(main_launcher_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Done! VK notification added to main_launcher.py")
