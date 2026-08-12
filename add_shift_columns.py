# -*- coding: utf-8 -*-
"""
Миграция: Добавить колонки для закрытия смены в work_sessions
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')

print(f"База данных: {DB_PATH}")

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Проверяем существующие колонки
cursor.execute("PRAGMA table_info(work_sessions)")
columns = {col[1] for col in cursor.fetchall()}
print(f"\nСуществующие колонки: {columns}")

# Добавляем недостающие колонки
migrations = [
    ('terminal_actual', 'REAL DEFAULT 0'),
    ('evening_cashless', 'REAL DEFAULT 0'),
]

for col_name, col_type in migrations:
    if col_name not in columns:
        print(f"Добавляем колонку: {col_name}")
        cursor.execute(f'ALTER TABLE work_sessions ADD COLUMN {col_name} {col_type}')
    else:
        print(f"Колонка {col_name} уже существует")

db.commit()
db.close()

print("\n✅ Миграция завершена!")
