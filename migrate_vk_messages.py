"""
Миграция VK сообщений из topic_id=1 в topic_id=3
VK сообщения должны быть в отдельной теме VK (topic_id=3)
"""
import sqlite3

conn = sqlite3.connect('schedule.db')
cursor = conn.cursor()

# Находим VK сообщения в topic_id=1 (username начинается с vk_user_)
cursor.execute('''
    SELECT id, username FROM chat_messages
    WHERE topic_id = 1 AND username LIKE 'vk_user_%'
''')
vk_messages_in_general = cursor.fetchall()

print(f"Найдено VK сообщений в topic_id=1: {len(vk_messages_in_general)}")

if vk_messages_in_general:
    # Перемещаем в topic_id=3
    cursor.executemany('''
        UPDATE chat_messages SET topic_id = 3 WHERE id = ?
    ''', [(msg[0],) for msg in vk_messages_in_general])
    conn.commit()
    print(f"✅ Перемещено {len(vk_messages_in_general)} сообщений в topic_id=3")

# Проверяем итог
cursor.execute('SELECT topic_id, COUNT(*) FROM chat_messages GROUP BY topic_id ORDER BY topic_id')
print("\nСообщения по темам:")
for row in cursor.fetchall():
    print(f"  topic_id={row[0]}: {row[1]} сообщений")

# Проверяем VK тему
cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE topic_id = 3')
vk_count = cursor.fetchone()[0]
print(f"\n✅ VK чат (topic_id=3): {vk_count} сообщений")

# Показываем последние 5 VK сообщений
cursor.execute('''
    SELECT id, username, message, created_at FROM chat_messages
    WHERE topic_id = 3 ORDER BY id DESC LIMIT 5
''')
print("\nПоследние 5 VK сообщений:")
for row in cursor.fetchall():
    print(f"  ID:{row[0]}, user:{row[1]}, msg:{row[2][:50]}, time:{row[3]}")

conn.close()
