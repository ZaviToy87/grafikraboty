# -*- coding: utf-8 -*-
"""
create_revision_transactions.py — Создание таблицы журнала операций с товарами
"""
import sqlite3
from datetime import datetime

DB_PATH = 'schedule.db'

def create_table():
    print("=" * 70)
    print("📋 СОЗДАНИЕ ТАБЛИЦЫ revision_transactions")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица журнала операций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revision_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            revision_id INTEGER NOT NULL,              -- Ссылка на товар
            user_id INTEGER NOT NULL,                  -- Кто выполнил операцию
            full_name TEXT NOT NULL,                   -- ФИО сотрудника
            
            action TEXT NOT NULL,                      -- Тип операции: sold/written_off/transferred/price_changed
            quantity INTEGER NOT NULL DEFAULT 1,       -- Количество
            price REAL,                                -- Цена продажи (может отличаться от retail_price)
            reason TEXT,                               -- Причина (для списания/переноса)
            
            quantity_before INTEGER,                   -- Количество до операции
            quantity_after INTEGER,                    -- Количество после операции
            
            notes TEXT,                                -- Примечания
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (revision_id) REFERENCES product_revisions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Индексы для быстрого поиска
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transactions_revision 
        ON revision_transactions(revision_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transactions_user 
        ON revision_transactions(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transactions_action 
        ON revision_transactions(action)
    ''')
    
    conn.commit()
    
    # Проверяем что таблица создана
    cursor.execute('SELECT COUNT(*) FROM revision_transactions')
    count = cursor.fetchone()[0]
    
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="revision_transactions"')
    table = cursor.fetchone()
    
    print(f"✅ Таблица revision_transactions создана: {table is not None}")
    print(f"📊 Записей в таблице: {count}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ ГОТОВО")
    print("=" * 70)

if __name__ == '__main__':
    create_table()
