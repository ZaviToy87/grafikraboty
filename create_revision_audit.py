# -*- coding: utf-8 -*-
"""
Скрипт создания таблицы аудита для ревизии товаров
"""
import sqlite3

DB_PATH = 'schedule.db'

def create_audit_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revision_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            revision_id INTEGER,
            user_id INTEGER,
            full_name TEXT,
            action TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (revision_id) REFERENCES product_revisions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Индекс для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_revision ON revision_audit_log(revision_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON revision_audit_log(user_id)')
    
    conn.commit()
    conn.close()
    print("✅ Таблица revision_audit_log создана успешно!")

if __name__ == '__main__':
    create_audit_table()
