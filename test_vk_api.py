"""
Тест VK API и Long Poll
Проверяет:
1. Работает ли сервисный токен
2. Возвращает ли Long Poll сервер
3. Есть ли события message_new
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
chat_peer_id = config.get('chat_peer_id')

print("=" * 60)
print("ТЕСТ VK API")
print("=" * 60)
print(f"Group ID: {group_id}")
print(f"Chat Peer ID: {chat_peer_id}")
print(f"Token: {token[:30]}...")

# Тест 1: Проверка токена через groups.getById
print("\n" + "=" * 60)
print("ТЕСТ 1: Проверка токена (groups.getById)")
print("=" * 60)

url = f'https://api.vk.com/method/groups.getById?group_id={group_id}&access_token={token}&v=5.131'
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Response: {data}")
        if 'response' in data and len(data['response']) > 0:
            group = data['response'][0]
            print(f"✅ Группа найдена: {group.get('name')}")
        elif 'error' in data:
            print(f"❌ Ошибка VK API: {data['error'].get('error_msg')}")
        else:
            print(f"❌ Группа не найдена")
except Exception as e:
    print(f"❌ Ошибка запроса: {e}")

# Тест 2: Получение Long Poll сервера
print("\n" + "=" * 60)
print("ТЕСТ 2: Инициализация Long Poll (groups.getLongPollServer)")
print("=" * 60)

url = f'https://api.vk.com/method/groups.getLongPollServer?group_id={group_id}&access_token={token}&v=5.131'
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Response: {data}")
        if 'response' in data:
            server = data['response'].get('server')
            key = data['response'].get('key')
            ts = data['response'].get('ts')
            print(f"✅ Long Poll сервер получен")
            print(f"   Server: {server}")
            print(f"   Key: {key[:20]}...")
            print(f"   TS: {ts}")
            
            # Тест 3: Проверка Long Poll
            print("\n" + "=" * 60)
            print("ТЕСТ 3: Long Poll запрос (ждем 5 сек)")
            print("=" * 60)
            
            poll_url = f"{server}?act=a_check&key={key}&ts={ts}&wait=5&version=5.208"
            print(f"URL: {poll_url[:80]}...")
            
            req = urllib.request.Request(poll_url)
            try:
                with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
                    poll_data = json.loads(resp.read().decode('utf-8'))
                    print(f"Response: {json.dumps(poll_data, indent=2, ensure_ascii=False)}")
                    
                    updates = poll_data.get('updates', [])
                    failed = poll_data.get('failed', 0)
                    
                    if failed:
                        print(f"⚠️ Long Poll failed (код {failed}) - нужно переинициализировать")
                    elif updates:
                        print(f"✅ Получено {len(updates)} событий:")
                        for upd in updates:
                            print(f"   - {upd.get('type')} (от {upd.get('object', {}).get('message', {}).get('from_id', '?')})")
                    else:
                        print(f"ℹ️ Событий нет (это нормально если никто не писал)")
                        
            except Exception as e:
                print(f"❌ Ошибка Long Poll: {e}")
        elif 'error' in data:
            print(f"❌ Ошибка VK API: {data['error'].get('error_msg')}")
        else:
            print(f"❌ Не удалось получить Long Poll сервер")
except Exception as e:
    print(f"❌ Ошибка запроса: {e}")

# Тест 4: Проверка участников чата
print("\n" + "=" * 60)
print("ТЕСТ 4: Участники чата (messages.getConversationMembers)")
print("=" * 60)

url = f'https://api.vk.com/method/messages.getConversationMembers?peer_id={chat_peer_id}&access_token={token}&v=5.131'
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        if 'response' in data:
            items = data['response'].get('items', [])
            count = data['response'].get('count', len(items))
            print(f"✅ Найдено {count} участников:")
            for item in items[:5]:  # Показываем первых 5
                member_id = item.get('member_id')
                first_name = item.get('first_name', '')
                last_name = item.get('last_name', '')
                print(f"   - VK ID: {member_id}, Имя: {first_name} {last_name}")
            if len(items) > 5:
                print(f"   ... и ещё {len(items) - 5} участников")
        elif 'error' in data:
            print(f"❌ Ошибка VK API: {data['error'].get('error_msg')}")
        else:
            print(f"❌ Не удалось получить участников")
except Exception as e:
    print(f"❌ Ошибка запроса: {e}")

print("\n" + "=" * 60)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 60)
