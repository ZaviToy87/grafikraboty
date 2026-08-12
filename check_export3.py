# -*- coding: utf-8 -*-
import sqlite3

db = sqlite3.connect('grafikraboty.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Структура work_schedule
cursor.execute("PRAGMA table_info(work_schedule)")
cols = cursor.fetchall()
print('=== work_schedule ===')
for c in cols:
    print(f"  {c['name']} ({c['type']})")

# Данные
cursor.execute("SELECT * FROM work_schedule LIMIT 5")
rows = cursor.fetchall()
print('\n=== sample data ===')
for r in rows:
    print(dict(r))

# Проверяем tasks
cursor.execute("PRAGMA table_info(tasks)")
cols = cursor.fetchall()
print('\n=== tasks ===')
for c in cols:
    print(f"  {c['name']} ({c['type']})")

cursor.execute("SELECT * FROM tasks LIMIT 5")
rows = cursor.fetchall()
print('\n=== tasks data ===')
for r in rows:
    print(dict(r))

# Проверяем users
cursor.execute("PRAGMA table_info(users)")
cols = cursor.fetchall()
print('\n=== users ===')
for c in cols:
    print(f"  {c['name']} ({c['type']})")

db.close()
print('\nDONE')
