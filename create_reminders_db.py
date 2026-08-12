# -*- coding: utf-8 -*-
"""
Скрипт создания таблицы напоминаний
"""
import sqlite3

DB_PATH = 'schedule.db'

def create_reminders_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Тип напоминания
            reminder_type TEXT DEFAULT 'general',
            -- general, revision, schedule, task
            
            -- Срок действия
            expires_at TIMESTAMP,
            
            -- Обязательно ли подтверждение
            require_confirmation INTEGER DEFAULT 1,
            
            -- Статистика прочтений
            total_users INTEGER DEFAULT 0,
            confirmed_users INTEGER DEFAULT 0,
            
            -- Активно ли
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Таблица подтверждений пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminder_confirmations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (reminder_id) REFERENCES reminders(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(reminder_id, user_id)  -- Один пользователь = одно подтверждение
        )
    ''')
    
    # Индексы
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_type ON reminders(reminder_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_confirmations_user ON reminder_confirmations(user_id)')
    
    conn.commit()
    conn.close()
    print("✅ Таблицы reminders и reminder_confirmations созданы успешно!")

if __name__ == '__main__':
    create_reminders_table()
