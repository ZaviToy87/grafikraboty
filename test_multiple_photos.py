# -*- coding: utf-8 -*-
"""
Тест множественных фото VK
Проверка всей цепочки: VK → Бот → Веб-чат
"""
import sqlite3
import os

DB_PATH = 'schedule.db'

print("=" * 70)
print(" ТЕСТ МНОЖЕСТВЕННЫХ ФОТО VK")
print("=" * 70)
print()

# Проверяем БД
print("1️⃣ Проверка таблицы chat_messages:")
if not os.path.exists(DB_PATH):
    print(f"  ❌ БД не найдена: {DB_PATH}")
else:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем колонки
    cursor.execute("PRAGMA table_info(chat_messages)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"  ✅ Колонки: {', '.join(columns)}")
    
    # Считаем сообщения с вложениями
    cursor.execute('''
        SELECT COUNT(*) FROM chat_messages 
        WHERE attachment_file_id IS NOT NULL
    ''')
    count = cursor.fetchone()[0]
    print(f"  ✅ Сообщений с вложениями: {count}")
    
    # Проверяем последние 10 сообщений с вложениями
    print()
    print("2️⃣ Последние 10 сообщений с вложениями:")
    cursor.execute('''
        SELECT id, username, full_name, message, attachment_file_id, 
               vk_conversation_id, created_at
        FROM chat_messages
        WHERE attachment_file_id IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            msg_id, username, full_name, message, file_id, vk_cid, created = row
            print(f"  ID:{msg_id} | {full_name} | Файл:{file_id} | VK:{vk_cid}")
    else:
        print("  ⚠️ Нет сообщений с вложениями")
    
    # Проверяем дубликаты
    print()
    print("3️⃣ Проверка на дубликаты:")
    cursor.execute('''
        SELECT vk_conversation_id, COUNT(*) as cnt
        FROM chat_messages
        WHERE vk_conversation_id IS NOT NULL
        GROUP BY vk_conversation_id
        HAVING cnt > 1
    ''')
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"  ❌ Найдены дубликаты:")
        for dup in duplicates:
            print(f"     {dup[0]}: {dup[1]} раз")
    else:
        print("  ✅ Дубликатов нет")
    
    # Проверяем файлы
    print()
    print("4️⃣ Проверка файлов:")
    cursor.execute('''
        SELECT COUNT(*) FROM files
        WHERE file_type LIKE '%image%'
    ''')
    img_count = cursor.fetchone()[0]
    print(f"  ✅ Изображений в БД: {img_count}")
    
    # Последние 5 файлов
    print()
    print("5️⃣ Последние 5 изображений:")
    cursor.execute('''
        SELECT id, filename, filepath, file_type, created_at
        FROM files
        WHERE file_type LIKE '%image%'
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    
    files = cursor.fetchall()
    if files:
        for f in files:
            fid, fname, fpath, ftype, fcreated = f
            exists = "✅" if os.path.exists(fpath) else "❌"
            print(f"  {exists} ID:{fid} | {fname} | {fpath}")
    else:
        print("  ⚠️ Нет изображений")
    
    conn.close()

print()
print("=" * 70)
print(" ИНСТРУКЦИЯ ПО ПРОВЕРКЕ")
print("=" * 70)
print()
print("1. Отправь 3-5 фото в VK чат группы")
print("2. Подожди 10 секунд")
print("3. Проверь логи:")
print("   type logs\\web_server.log | findstr \"MULTIPLE\"")
print("4. Проверь веб-чат:")
print("   http://192.168.1.207:8080/chat")
print()
print("Если фото не появились — проверь логи vk_bot.log:")
print("   type logs\\vk_bot.log | findstr \"attachments\"")
print()
