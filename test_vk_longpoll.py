"""
Тест VK Long Poll v5.208
Проверяет что сообщения из VK чата приходят правильно
"""
import json
import urllib.request
import ssl
import time

# SSL контекст как в vk_bot.py
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Загружаем конфиг
with open('vk_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

token = config.get('service_token')
group_id = config.get('group_id')

print("=" * 70)
print("ТЕСТ VK LONG POLL v5.208")
print("=" * 70)

# Шаг 1: Получаем Long Poll сервер
print("\n📡 ШАГ 1: Получение Long Poll сервера...")
url = f'https://api.vk.com/method/groups.getLongPollServer?group_id={group_id}&access_token={token}&v=5.208'
req = urllib.request.Request(url)

with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    
if 'response' not in data:
    print(f"❌ Ошибка: {data}")
    exit(1)

server = data['response'].get('server')
key = data['response'].get('key')
ts = data['response'].get('ts')

print(f"✅ Server: {server}")
print(f"✅ Key: {key[:30]}...")
print(f"✅ TS: {ts}")

# Шаг 2: Делаем Long Poll запрос и ждём сообщения
print("\n⏳ ШАГ 2: Ожидание событий (15 секунд)...")
print("💡 Напиши сообщение в VK чат прямо сейчас!")
print()

poll_url = f"{server}?act=a_check&key={key}&ts={ts}&wait=15&version=5.208"

start_time = time.time()
req = urllib.request.Request(poll_url)

try:
    with urllib.request.urlopen(req, timeout=20, context=ssl_context) as resp:
        elapsed = time.time() - start_time
        data = json.loads(resp.read().decode('utf-8'))
        
        print(f"⏱️  Получено через {elapsed:.1f} сек")
        print(f"📦 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        updates = data.get('updates', [])
        failed = data.get('failed', 0)
        
        if failed:
            print(f"\n⚠️ Long Poll failed (код {failed})")
            print("   Нужно переинициализировать сервер")
        elif updates:
            print(f"\n✅ ПОЛУЧЕНО {len(updates)} СОБЫТИЙ:")
            for i, event in enumerate(updates):
                event_type = event.get('type')
                event_obj = event.get('object', {})
                
                print(f"\n📨 Событие {i+1}: {event_type}")
                print(f"   Объект ключи: {list(event_obj.keys())}")
                
                # Извлекаем message (пробуем разные варианты)
                message = event_obj.get('message', {})
                if not message:
                    message = event_obj
                
                from_id = message.get('from_id')
                text = message.get('text', '')
                peer_id = message.get('peer_id')
                
                print(f"   From ID: {from_id}")
                print(f"   Peer ID: {peer_id}")
                print(f"   Text: {text[:100]}")
                
                if event_type == 'message_new':
                    print(f"   ✅ ЭТО ВХОДЯЩЕЕ СООБЩЕНИЕ!")
                    print(f"   _process_message_event() должен его обработать")
        else:
            print("\nℹ️ Событий нет")
            print("   Это нормально если никто не писал в чат")
            print("   Попробуй написать сообщение в VK чат и запусти тест снова")
            
except urllib.error.URLError as e:
    print(f"❌ Ошибка соединения: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n" + "=" * 70)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 70)
print("\n💡 Если сообщения приходят — Long Poll работает правильно!")
print("   Перезапусти сервер GrafikRaboty для применения изменений")
