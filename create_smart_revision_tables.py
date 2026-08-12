# -*- coding: utf-8 -*-
"""
create_smart_revision_tables.py — Создание таблиц для умной системы ревизии
"""

import sqlite3
from datetime import datetime

DB_PATH = 'schedule.db'

def create_smart_tables():
    print("=" * 70)
    print("📋 СОЗДАНИЕ ТАБЛИЦ ДЛЯ УМНОЙ СИСТЕМЫ РЕВИЗИИ")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Таблица умных напоминаний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS smart_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            revision_id INTEGER,                      -- Ссылка на товар (может быть NULL)
            user_id INTEGER,                          -- Для кого напоминание (NULL = для всех/админа)
            
            reminder_type TEXT NOT NULL,              -- Тип: expiring_soon, stale_high_discount, admin_decision, personal_summary
            title TEXT NOT NULL,                      -- Заголовок напоминания
            message TEXT NOT NULL,                    -- Текст напоминания
            priority TEXT DEFAULT 'medium',           -- urgent, high, medium, low
            
            status TEXT DEFAULT 'pending',            -- pending, completed, dismissed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            completed_by INTEGER,                     -- Кто отметил как выполненное
            
            FOREIGN KEY (revision_id) REFERENCES product_revisions(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (completed_by) REFERENCES users(id)
        )
    ''')
    
    # 2. Добавляем новые колонки в таблицу product_revisions для умных напоминаний
    try:
        # Проверяем существование колонок
        cursor.execute("PRAGMA table_info(product_revisions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = [
            ('expiry_reminder_sent', 'INTEGER DEFAULT 0'),
            ('last_sale_reminder', 'TIMESTAMP'),
            ('admin_decision_reminder_sent', 'INTEGER DEFAULT 0'),
            ('last_personal_reminder', 'TIMESTAMP'),
            ('last_operation', 'TIMESTAMP')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                cursor.execute(f'ALTER TABLE product_revisions ADD COLUMN {col_name} {col_type}')
                print(f"✅ Добавлена колонка: {col_name}")
    
    except Exception as e:
        print(f"⚠️ Ошибка при добавлении колонок: {e}")
    
    # 3. Создаем индексы для быстрого поиска
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_smart_reminders_user 
        ON smart_reminders(user_id, status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_smart_reminders_type 
        ON smart_reminders(reminder_type, priority)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_product_revisions_expiry 
        ON product_revisions(days_remaining, status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_product_revisions_discount 
        ON product_revisions(discount_percent, status)
    ''')
    
    conn.commit()
    
    # Проверяем созданные таблицы
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n📊 Созданные таблицы:")
    for table in sorted(tables):
        if 'revision' in table.lower() or 'smart' in table.lower() or 'reminder' in table.lower():
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  • {table}: {count} записей")
    
    # Проверяем колонки product_revisions
    print("\n📋 Колонки product_revisions:")
    cursor.execute("PRAGMA table_info(product_revisions)")
    for col in cursor.fetchall():
        if col[1] in ['expiry_reminder_sent', 'last_sale_reminder', 'admin_decision_reminder_sent', 'last_personal_reminder']:
            print(f"  • {col[1]} ({col[2]}) - {'✅' if col[1] in columns else '❌'}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ УМНАЯ СИСТЕМА РЕВИЗИИ ГОТОВА К ИСПОЛЬЗОВАНИЮ")
    print("=" * 70)
    print("\n📈 Функции системы:")
    print("  1. Расширенная статистика по всем типам операций")
    print("  2. Умные напоминания с триггерами:")
    print("     • Товары скоро истекают (за 7 дней)")
    print("     • Товары с большой скидкой не продаются")
    print("     • Требуются решения администратора")
    print("     • Персональные напоминания продавцам")
    print("  3. Автоматические отчеты в VK чат")
    print("  4. Панель управления с аналитикой")
    print("\n🚀 Для запуска системы добавьте в web_server.py:")
    print("   from smart_revision_system import smart_bp")
    print("   app.register_blueprint(smart_bp)")

def update_existing_data():
    """
    Обновить существующие данные для совместимости с умной системой
    """
    print("\n" + "=" * 70)
    print("🔄 ОБНОВЛЕНИЕ СУЩЕСТВУЮЩИХ ДАННЫХ")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Обновляем last_operation для товаров
    print("📊 Обновление даты последней операции для товаров...")
    cursor.execute('''
        UPDATE product_revisions 
        SET last_operation = (
            SELECT MAX(created_at) 
            FROM revision_transactions 
            WHERE revision_id = product_revisions.id
        )
        WHERE EXISTS (
            SELECT 1 FROM revision_transactions 
            WHERE revision_id = product_revisions.id
        )
    ''')
    
    updated = cursor.rowcount
    print(f"✅ Обновлено {updated} товаров")
    
    # 2. Сбрасываем флаги напоминаний для активных товаров
    print("\n🔄 Сброс флагов напоминаний...")
    cursor.execute('''
        UPDATE product_revisions 
        SET expiry_reminder_sent = 0,
            admin_decision_reminder_sent = 0
        WHERE status IN ('active', 'admin_decision')
    ''')
    
    reset = cursor.rowcount
    print(f"✅ Сброшены флаги для {reset} товаров")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
    print("=" * 70)

if __name__ == '__main__':
    create_smart_tables()
    update_existing_data()
    
    print("\n🎯 Следующие шаги:")
    print("1. Добавьте импорт smart_revision_system в web_server.py")
    print("2. Добавьте планировщик для ежедневных проверок")
    print("3. Обновите интерфейс для отображения умной статистики")
    print("4. Протестируйте систему через API:")
    print("   • GET /smart/stats")
    print("   • GET /smart/reminders")
    print("   • GET /smart/dashboard")
    print("   • POST /smart/check-reminders (админ)")