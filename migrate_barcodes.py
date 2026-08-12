# -*- coding: utf-8 -*-
"""
Миграция barcodes для всех баз данных GrafikRaboty
"""
import sqlite3
import os

def migrate_db(db_path):
    """Применить миграцию barcodes к базе данных."""
    if not os.path.exists(db_path):
        print(f"  ⚠️  БД не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли таблица
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='barcodes'")
        if cursor.fetchone():
            print(f"  ✅ barcodes уже есть: {db_path}")
            conn.close()
            return True
        
        # Создаём таблицу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS barcodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                factory_barcode TEXT,
                internal_barcode TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcodes_internal ON barcodes(internal_barcode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcodes_factory ON barcodes(factory_barcode)')
        conn.commit()
        conn.close()
        print(f"  ✅ barcodes создана: {db_path}")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("МИГРАЦИЯ BARCODES ДЛЯ ВСЕХ БД GrafikRaboty")
    print("=" * 60)
    
    # БД в папке проекта
    desktop_db = r"C:\Users\User\Desktop\GrafikRaboty\schedule.db"
    
    # БД в AppData
    appdata_db = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GrafikRaboty', 'schedule.db')
    
    print("\nПроверка баз данных...")
    migrate_db(desktop_db)
    migrate_db(appdata_db)
    
    print("\n" + "=" * 60)
    print("Миграция завершена!")
    print("=" * 60)
