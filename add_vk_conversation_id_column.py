# -*- coding: utf-8 -*-
"""
Миграция: Добавить колонку vk_conversation_id для защиты от дубликатов
"""
import sqlite3
import os

# Пути к БД
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')

def migrate():
    """Добавить колонку vk_conversation_id в chat_messages"""
    
    print("=" * 60)
    print(" МИГРАЦИЯ: vk_conversation_id")
    print("=" * 60)
    print()
    
    if not os.path.exists(DB_PATH):
        print(f"❌ БД не найдена: {DB_PATH}")
        return
    
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # Проверяем, существует ли уже колонка
    cursor.execute("PRAGMA table_info(chat_messages)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"📋 Текущие колонки в chat_messages:")
    for col in columns:
        print(f"  - {col}")
    print()
    
    if 'vk_conversation_id' in columns:
        print("✅ Колонка vk_conversation_id уже существует")
    else:
        print("➕ Добавление колонки vk_conversation_id...")
        cursor.execute('''
            ALTER TABLE chat_messages 
            ADD COLUMN vk_conversation_id TEXT
        ''')
        db.commit()
        print("✅ Колонка добавлена")
    
    # Создаём индекс для ускорения проверки дубликатов
    print()
    print("📊 Создание индекса idx_vk_conversation...")
    try:
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_vk_conversation 
            ON chat_messages(vk_conversation_id)
        ''')
        db.commit()
        print("✅ Индекс создан")
    except Exception as e:
        print(f"⚠️ Ошибка создания индекса: {e}")
    
    # Заполняем существующие записи NULL (они не будут считаться дубликатами)
    print()
    print("📝 Обновление существующих записей...")
    cursor.execute('''
        UPDATE chat_messages 
        SET vk_conversation_id = NULL 
        WHERE vk_conversation_id IS NULL
    ''')
    db.commit()
    print(f"✅ Записей обновлено: {cursor.rowcount}")
    
    db.close()
    
    print()
    print("=" * 60)
    print(" ✅ МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)
    print()
    print("Теперь дубликаты сообщений VK будут блокироваться!")

if __name__ == '__main__':
    migrate()
