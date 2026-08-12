import sqlite3

def check_database():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    
    print("=== Проверка структуры базы данных ===")
    
    # 1. Проверяем таблицу product_revisions
    print("\n1. Таблица product_revisions:")
    cursor.execute("PRAGMA table_info(product_revisions)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Проверяем наличие колонки updated_at
    has_updated_at = any(col[1] == 'updated_at' for col in columns)
    print(f"\n  Колонка 'updated_at' существует: {has_updated_at}")
    
    # 2. Проверяем таблицу revision_transactions
    print("\n2. Таблица revision_transactions:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='revision_transactions'")
    table = cursor.fetchone()
    
    if table:
        print(f"  Таблица существует")
        cursor.execute("PRAGMA table_info(revision_transactions)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("  Таблица НЕ существует!")
    
    # 3. Проверяем таблицу revision_audit_log
    print("\n3. Таблица revision_audit_log:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='revision_audit_log'")
    table = cursor.fetchone()
    
    if table:
        print(f"  Таблица существует")
        cursor.execute("PRAGMA table_info(revision_audit_log)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("  Таблица НЕ существует!")
    
    conn.close()

if __name__ == "__main__":
    check_database()