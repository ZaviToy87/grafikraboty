# -*- coding: utf-8 -*-
import sqlite3

db = sqlite3.connect('grafikraboty.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Все таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print('=== ALL TABLES ===')
for t in tables:
    print(t['name'])

# Ищем таблицы связанные с графиком
for t in tables:
    name = t['name']
    if 'schedule' in name.lower() or 'shift' in name.lower() or 'work' in name.lower() or 'graph' in name.lower():
        print(f'\n=== {name} ===')
        cursor.execute(f"PRAGMA table_info({name})")
        cols = cursor.fetchall()
        for c in cols:
            print(f"  {c['name']} ({c['type']})")
        try:
            cursor.execute(f"SELECT * FROM {name} LIMIT 3")
            rows = cursor.fetchall()
            for r in rows:
                print(f"  -> {dict(r)}")
        except Exception as e:
            print(f"  Error: {e}")

db.close()
print('\nDONE')
