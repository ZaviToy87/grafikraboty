import sqlite3
import datetime

def fix_database():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    print("=== Исправление структуры базы данных ===")
    
    # 1. Добавляем колонку updated_at в product_revisions если её нет
    cursor.execute("PRAGMA table_info(product_revisions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'updated_at' not in columns:
        print("Добавляем колонку 'updated_at' в таблицу 'product_revisions'...")
        try:
            cursor.execute("ALTER TABLE product_revisions ADD COLUMN updated_at TIMESTAMP")
            print("✅ Колонка 'updated_at' добавлена")
            
            # Устанавливаем значение по умолчанию для существующих записей
            cursor.execute("UPDATE product_revisions SET updated_at = created_at WHERE updated_at IS NULL")
            conn.commit()
            print("✅ Значения 'updated_at' обновлены")
        except Exception as e:
            print(f"❌ Ошибка при добавлении колонки: {e}")
            conn.rollback()
    else:
        print("✅ Колонка 'updated_at' уже существует")
    
    # 2. Проверяем наличие индексов
    print("\nПроверка индексов...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%revision%'")
    indexes = cursor.fetchall()
    print(f"Найдено индексов для ревизии: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx[0]}")
    
    conn.close()
    print("\n✅ Проверка завершена")

if __name__ == "__main__":
    fix_database()