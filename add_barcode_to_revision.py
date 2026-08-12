# -*- coding: utf-8 -*-
"""
Добавить поле barcode в таблицу product_revisions
"""
import sqlite3

DB_PATH = 'schedule.db'

def add_barcode_field():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем существует ли колонка
    cursor.execute('PRAGMA table_info(product_revisions)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'barcode' not in columns:
        cursor.execute('ALTER TABLE product_revisions ADD COLUMN barcode TEXT')
        conn.commit()
        print("✅ Поле barcode добавлено в product_revisions")
    else:
        print("ℹ️ Поле barcode уже существует")
    
    conn.close()

if __name__ == '__main__':
    add_barcode_field()
