# -*- coding: utf-8 -*-
"""
Скрипт исправления проблем БД
"""
import sqlite3
import os

DB_PATH = 'schedule.db'

def fix_work_journal_entries():
    """Добавляет колонку user_id в таблицу work_journal_entries"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем есть ли уже колонка
    cursor.execute('PRAGMA table_info(work_journal_entries)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'user_id' not in columns:
        print("✓ Добавляем колонку user_id в work_journal_entries...")
        cursor.execute('ALTER TABLE work_journal_entries ADD COLUMN user_id INTEGER')
        
        # Обновляем существующие записи — берём user_id из связанной смены
        cursor.execute('''
            UPDATE work_journal_entries
            SET user_id = (
                SELECT user_id FROM work_journal_shift
                WHERE work_journal_shift.id = work_journal_entries.shift_id
            )
            WHERE user_id IS NULL
        ''')
        
        conn.commit()
        print("✓ Колонка user_id добавлена")
    else:
        print("✓ Колонка user_id уже существует")
    
    conn.close()

def fix_files_unique_constraint():
    """Убирает UNIQUE constraint с files.filepath"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем текущую структуру
    cursor.execute('PRAGMA table_info(files)')
    columns = cursor.fetchall()
    
    # Проверяем индексы
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='files'")
    indexes = cursor.fetchall()
    
    # Ищем уникальный индекс на filepath
    unique_idx = None
    for name, sql in indexes:
        if sql and 'UNIQUE' in sql.upper() and 'filepath' in sql:
            unique_idx = name
            break
    
    if unique_idx:
        print(f"✓ Удаляем уникальный индекс {unique_idx}...")
        cursor.execute(f'DROP INDEX IF EXISTS {unique_idx}')
        conn.commit()
        print("✓ Уникальный индекс удалён")
    else:
        print("✓ Уникальный индекс на filepath не найден")
    
    conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("ИСПРАВЛЕНИЕ ПРОБЛЕМ БД")
    print("=" * 50)
    
    fix_work_journal_entries()
    fix_files_unique_constraint()
    
    print("=" * 50)
    print("✓ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ")
    print("=" * 50)
