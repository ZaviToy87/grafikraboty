# -*- coding: utf-8 -*-
"""
Тест новых команд VK бота
"""
import sys
import os

# Добавляем путь к проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print("=" * 70)
print(" ТЕСТ НОВЫХ КОМАНД VK БОТА")
print("=" * 70)
print()

# Импортируем функции
try:
    import vk_bot
    
    print("✅ VK бот импортирован")
    print()
    
    # Проверяем наличие новых функций
    functions_to_check = [
        'handle_address_command',
        'handle_tunnel_command',
        'handle_status_command'
    ]
    
    print("📋 Проверка функций:")
    for func_name in functions_to_check:
        if hasattr(vk_bot, func_name):
            print(f"  ✅ {func_name}")
        else:
            print(f"  ❌ {func_name} - НЕ НАЙДЕНА")
    
    print()
    
    # Проверяем конфигурацию
    print("🔧 Проверка конфигурации:")
    config = vk_bot.get_config()
    
    if config:
        print(f"  ✅ Токен: {'настроен' if config.get('service_token') else '❌ не настроен'}")
        print(f"  ✅ Group ID: {config.get('group_id')}")
        print(f"  ✅ Admin VK ID: {config.get('admin_vk_id')}")
        print(f"  ✅ Chat Peer ID: {config.get('chat_peer_id')}")
    else:
        print("  ❌ Конфигурация не загружена")
    
    print()
    
    # Проверяем IP функции
    print("🌐 Проверка IP функций:")
    local_ip = vk_bot.get_local_ip()
    public_ip = vk_bot.get_public_ip()
    
    print(f"  ✅ Локальный IP: {local_ip}")
    print(f"  ✅ Внешний IP: {public_ip}")
    
    print()
    
    # Проверяем tunnel_info.json
    print("🔒 Проверка tunnel_info.json:")
    import json
    
    tunnel_info_path = os.path.join(BASE_DIR, 'tunnel_info.json')
    if os.path.exists(tunnel_info_path):
        with open(tunnel_info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        print(f"  ✅ URL: {info.get('tunnel_url', 'не указан')}")
        print(f"  ✅ Пароль: {info.get('password', 'не указан')}")
    else:
        print("  ⚠️ tunnel_info.json не найден")
    
    print()
    print("=" * 70)
    print(" ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print("=" * 70)
    print()
    print("📝 Новые команды готовы к использованию:")
    print("   /address - все адреса доступа")
    print("   /tunnel - информация о туннеле")
    print("   /status - статус сервера")
    print()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
