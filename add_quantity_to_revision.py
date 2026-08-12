# -*- coding: utf-8 -*-
"""
Добавить поле quantity в таблицу product_revisions
"""
import sqlite3

DB_PATH = 'schedule.db'

def add_quantity_field():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем существует ли колонка
    cursor.execute('PRAGMA table_info(product_revisions)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'quantity' not in columns:
        cursor.execute('ALTER TABLE product_revisions ADD COLUMN quantity INTEGER DEFAULT 1')
        conn.commit()
        print("✅ Поле quantity добавлено в product_revisions")
    else:
        print("ℹ️ Поле quantity уже существует")
    
    conn.close()

if __name__ == '__main__':
    add_quantity_field()
