import sqlite3
import sys

src_path = 'grafikraboty.db'
dst_path = 'schedule.db'

try:
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dst_path)
    
    # Получаем список sync_ таблиц
    tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sync_%'").fetchall()]
    print(f"Найдено таблиц: {len(tables)}")
    
    for table in tables:
        # Удаляем старую таблицу если есть
        dst.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Получаем CREATE TABLE
        create_sql = src.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'").fetchone()[0]
        print(f"Создаю {table}...")
        dst.execute(create_sql)
        
        # Копируем данные
        rows = src.execute(f'SELECT * FROM {table}').fetchall()
        if rows:
            cols_info = src.execute(f'PRAGMA table_info({table})').fetchall()
            col_names = ','.join([c[1] for c in cols_info])
            placeholders = ','.join(['?' for _ in cols_info])
            dst.executemany(f'INSERT INTO {table} ({col_names}) VALUES ({placeholders})', rows)
        
        count = dst.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'  {table}: {count} rows')
    
    dst.commit()
    print('Готово!')
except Exception as e:
    print(f'ОШИБКА: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    src.close()
    dst.close()
