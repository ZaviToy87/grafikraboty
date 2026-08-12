# -*- coding: utf-8 -*-
import sqlite3

db = sqlite3.connect('grafikraboty.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Проверяем структуру таблицы schedule
cursor.execute("PRAGMA table_info(schedule)")
cols = cursor.fetchall()
print('=== schedule table ===')
for c in cols:
    print(c)

# Проверяем есть ли task_ids
try:
    cursor.execute('SELECT task_ids FROM schedule LIMIT 3')
    rows = cursor.fetchall()
    print('\n=== sample task_ids ===')
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f'\nError: {e}')

# Проверяем структуру таблицы schedule (альтернативные названия)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%schedule%' OR name LIKE '%Schedule%'")
tables = cursor.fetchall()
print('\n=== tables matching schedule ===')
for t in tables:
    print(t)

db.close()
print('\nDONE')
