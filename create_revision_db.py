# -*- coding: utf-8 -*-
"""
Скрипт создания таблицы для ревизии товаров
"""
import sqlite3
from datetime import datetime

DB_PATH = 'schedule.db'

def create_revision_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            product_name TEXT NOT NULL,
            retail_price REAL NOT NULL,
            expiry_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Авто-расчёт
            days_remaining INTEGER,
            discount_percent INTEGER DEFAULT 0,
            final_price REAL,
            
            -- Статус
            status TEXT DEFAULT 'active',
            -- Статусы: 'active', 'admin_decision', 'sold', 'reserved_admin', 'utilized'
            
            -- Решение админа
            admin_decision TEXT,
            admin_decision_at TIMESTAMP,
            admin_vk_id INTEGER,
            
            -- Для уведомлений
            notification_sent INTEGER DEFAULT 0,
            weekly_notified INTEGER DEFAULT 0,
            
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Индексы для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_revision_expiry ON product_revisions(expiry_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_revision_status ON product_revisions(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_revision_user ON product_revisions(user_id)')
    
    conn.commit()
    conn.close()
    print("✅ Таблица product_revisions создана успешно!")

if __name__ == '__main__':
    create_revision_table()
