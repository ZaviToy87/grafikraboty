# -*- coding: utf-8 -*-
"""
Тест VK синхронизации - проверка отправки сообщений в обе стороны
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import vk_bot
import json
import urllib.request
from datetime import datetime

print("=" * 60)
print("ТЕСТ VK СИНХРОНИЗАЦИИ")
print("=" * 60)

# Загружаем конфиг
config = vk_bot.get_config()
print(f"\n✓ Конфигурация:")
print(f"  Token: {'настроен' if config.get('service_token') else 'НЕ настроен'}")
print(f"  Group ID: {config.get('group_id')}")
print(f"  Chat Peer ID: {config.get('chat_peer_id')}")
print(f"  Admin VK ID: {config.get('admin_vk_id')}")
print(f"  VK User Map: {config.get('vk_user_map')}")

# ТЕСТ 1: Отправка сообщения из программы в VK
print("\n" + "=" * 60)
print("ТЕСТ 1: Отправка сообщения ИЗ программы в VK")
print("=" * 60)

test_message = f"[ТЕСТ АВТОМАТИЧЕСКИЙ] Сообщение отправлено в {datetime.now().strftime('%H:%M:%S')}"
print(f"\nТекст сообщения: {test_message}")

if config.get('chat_peer_id'):
    result = vk_bot.send_message(
        peer_id=int(config['chat_peer_id']),
        message=test_message
    )
    print(f"Результат: {'✓ ОТПРАВЛЕНО' if result else '✗ ОШИБКА'}")
else:
    print("✗ Chat Peer ID не настроен!")

# ТЕСТ 2: Проверка HTTP эндпоинта синхронизации
print("\n" + "=" * 60)
print("ТЕСТ 2: Проверка HTTP эндпоинта /api/vk-chat/vk-sync")
print("=" * 60)

test_event = {
    "message": {
        "from_id": -199112265,  # От имени группы (отрицательный)
        "peer_id": 2000000001,  # Чат группы
        "text": f"[ТЕСТ ВХОДЯЩЕЕ] Сообщение из VK в {datetime.now().strftime('%H:%M:%S')}",
        "conversation_message_id": 999999
    }
}

try:
    sync_url = 'http://127.0.0.1:8080/api/vk-chat/vk-sync'
    data = json.dumps({'event': test_event}).encode('utf-8')
    req = urllib.request.Request(
        sync_url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f"✓ Эндпоинт отвечает: {result}")
except Exception as e:
    print(f"✗ Ошибка подключения к эндпоинту: {e}")
    print("  Убедитесь, что сервер запущен на порту 8080")

# ТЕСТ 3: Проверка с вложениями (фото)
print("\n" + "=" * 60)
print("ТЕСТ 3: Отправка фото в VK")
print("=" * 60)

# Создаём тестовое изображение
test_image_path = os.path.join(os.path.dirname(__file__), 'test_image.png')
try:
    # Создаём простой PNG (1x1 пиксель)
    import struct
    import zlib
    
    def create_minimal_png(filename):
        """Создать минимальный PNG файл 10x10 пикселей красного цвета"""
        width, height = 10, 10
        
        def png_chunk(chunk_type, data):
            chunk_len = struct.pack('>I', len(data))
            chunk_crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
            return chunk_len + chunk_type + data + chunk_crc
        
        signature = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr = png_chunk(b'IHDR', ihdr_data)
        
        # Красные пиксели (RGB)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'  # фильтр None
            for x in range(width):
                raw_data += b'\xff\x00\x00'  # Красный цвет
        
        compressed = zlib.compress(raw_data)
        idat = png_chunk(b'IDAT', compressed)
        iend = png_chunk(b'IEND', b'')
        
        with open(filename, 'wb') as f:
            f.write(signature + ihdr + idat + iend)
    
    create_minimal_png(test_image_path)
    print(f"✓ Тестовое изображение создано: {test_image_path}")
    
    # Пробуем отправить фото
    if config.get('service_token'):
        print(f"\nОтправка фото в чат (peer_id={config.get('chat_peer_id')})...")
        result = vk_bot.upload_photo(test_image_path, peer_id=int(config['chat_peer_id']))
        print(f"Результат: {'✓ ФОТО ОТПРАВЛЕНО' if result else '✗ ОШИБКА ОТПРАВКИ'}")
    else:
        print("✗ Токен не настроен!")
        
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()

# ТЕСТ 4: Проверка Long Poll
print("\n" + "=" * 60)
print("ТЕСТ 4: Проверка Long Poll")
print("=" * 60)

if config.get('service_token'):
    print("Запуск Long Poll на 10 секунд для проверки получения сообщений...")
    print("Напишите сообщение в чат VK для проверки!")
    
    # Временный обработчик
    @vk_bot.on_message
    def test_handler(vk_id, user_id, peer_id, message, message_id, attachments=None, event_data=None):
        print(f"\n✓ ПОЛУЧЕНО СООБЩЕНИЕ ИЗ VK:")
        print(f"  VK ID: {vk_id}")
        print(f"  User ID: {user_id}")
        print(f"  Peer ID: {peer_id}")
        print(f"  Текст: {message}")
        print(f"  Вложения: {attachments}")
    
    # Запускаем polling
    vk_bot.start_polling()
    
    import time
    start_time = time.time()
    while time.time() - start_time < 10:
        time.sleep(1)
    
    vk_bot.stop_polling()
    print("\nLong Poll остановлен")
else:
    print("✗ Токен не настроен!")

print("\n" + "=" * 60)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 60)

# Удаляем тестовый файл
if os.path.exists(test_image_path):
    os.remove(test_image_path)
    print(f"Тестовый файл удалён: {test_image_path}")
