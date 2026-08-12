# -*- coding: utf-8 -*-
"""
migrate_work_sessions.py — Миграция для разделения графика и рабочих смен

Цель:
- schedule → work_schedule (планируемый график, кто ДОЛЖЕН работать)
- work_sessions (фактические смены, кто РЕАЛЬНО работал)
- work_journal_entries связывается с work_sessions, а не с графиком
"""
import sqlite3
from datetime import datetime

DB_PATH = 'schedule.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== НАЧАЛО МИГРАЦИИ ===")
    print(f"Время: {datetime.now().isoformat()}")
    
    # 1. Переименовываем schedule в work_schedule
    print("\n1. Переименование schedule → work_schedule...")
    try:
        cursor.execute('ALTER TABLE schedule RENAME TO work_schedule')
        print("   ✅ Таблица переименована")
    except Exception as e:
        if 'already exists' in str(e):
            print("   ⚠️ work_schedule уже существует")
        else:
            raise
    
    # 2. Создаём таблицу work_sessions (фактические смены)
    print("\n2. Создание таблицы work_sessions...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            work_schedule_id INTEGER,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            opened_at TIMESTAMP,
            closed_at TIMESTAMP,
            opening_sum REAL DEFAULT 0,
            closing_sum REAL DEFAULT 0,
            revenue_total REAL DEFAULT 0,
            acquiring_amount REAL DEFAULT 0,
            evening_cash REAL DEFAULT 0,
            evening_cashless REAL DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT 'opened',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (work_schedule_id) REFERENCES work_schedule(id) ON DELETE SET NULL
        )
    ''')
    print("   ✅ Таблица создана")
    
    # Индексы для work_sessions
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_sessions_user ON work_sessions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_sessions_date ON work_sessions(year, month, day)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_sessions_status ON work_sessions(status)')
    print("   ✅ Индексы созданы")
    
    # 3. Мигрируем существующие смены из work_schedule в work_sessions
    print("\n3. Миграция существующих смен...")
    cursor.execute('''
        SELECT id, user_id, year, month, day, task_ids, notes, created_at
        FROM work_schedule
        WHERE task_ids LIKE '%6%' OR task_ids LIKE '%Смена физическая%'
    ''')
    
    shifts = cursor.fetchall()
    migrated_count = 0
    
    for shift in shifts:
        # Проверяем, есть ли уже запись в work_sessions
        cursor.execute('''
            SELECT id FROM work_sessions
            WHERE user_id = ? AND year = ? AND month = ? AND day = ?
        ''', (shift['user_id'], shift['year'], shift['month'], shift['day']))
        
        if cursor.fetchone():
            continue  # Уже есть
        
        # Проверяем, есть ли записи в work_journal_entries для этой смены
        cursor.execute('''
            SELECT MIN(created_at) as first_entry, MAX(created_at) as last_entry
            FROM work_journal_entries
            WHERE shift_id = ?
        ''', (shift['id'],))
        
        entry = cursor.fetchone()
        
        # Определяем статус и суммы
        status = 'closed'
        opening_sum = 0
        closing_sum = 0
        
        if entry['first_entry']:
            # Получаем сумму открытия
            cursor.execute('''
                SELECT amount FROM work_journal_entries
                WHERE shift_id = ? AND kind = 'opening'
                ORDER BY created_at LIMIT 1
            ''', (shift['id'],))
            opening_entry = cursor.fetchone()
            if opening_entry:
                opening_sum = opening_entry['amount']
            
            # Проверяем наличие закрытия
            cursor.execute('''
                SELECT COUNT(*) as cnt FROM work_journal_entries
                WHERE shift_id = ? AND kind = 'closing'
            ''', (shift['id'],))
            if cursor.fetchone()['cnt'] > 0:
                status = 'closed'
                cursor.execute('''
                    SELECT amount FROM work_journal_entries
                    WHERE shift_id = ? AND kind = 'closing'
                    ORDER BY created_at DESC LIMIT 1
                ''', (shift['id'],))
                closing_entry = cursor.fetchone()
                if closing_entry:
                    closing_sum = closing_entry['amount']
            else:
                status = 'opened'
        
        # Создаём запись в work_sessions
        cursor.execute('''
            INSERT INTO work_sessions
            (user_id, work_schedule_id, year, month, day, opened_at, closed_at,
             opening_sum, closing_sum, status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            shift['user_id'],
            shift['id'],  # Связь с work_schedule
            shift['year'],
            shift['month'],
            shift['day'],
            entry['first_entry'],
            entry['last_entry'] if status == 'closed' else None,
            opening_sum,
            closing_sum,
            status,
            shift['notes'],
            shift['created_at']
        ))
        
        migrated_count += 1
    
    print(f"   ✅ Мигрировано смен: {migrated_count}")
    
    # 4. Обновляем work_journal_entries для связи с work_sessions
    print("\n4. Обновление связей work_journal_entries...")
    
    # Добавляем временную колонку old_shift_id для миграции
    try:
        cursor.execute('ALTER TABLE work_journal_entries ADD COLUMN old_shift_id INTEGER')
    except:
        pass  # Уже есть
    
    # Заполняем old_shift_id текущими значениями shift_id
    cursor.execute('UPDATE work_journal_entries SET old_shift_id = shift_id')
    
    # Создаём маппинг old_shift_id → new session_id
    cursor.execute('''
        SELECT id, user_id, year, month, day FROM work_schedule
        WHERE id IN (SELECT DISTINCT old_shift_id FROM work_journal_entries WHERE old_shift_id IS NOT NULL)
    ''')
    
    schedule_map = {row['id']: row for row in cursor.fetchall()}
    
    updated_count = 0
    for old_shift_id, schedule_data in schedule_map.items():
        # Находим соответствующую сессию
        cursor.execute('''
            SELECT id FROM work_sessions
            WHERE user_id = ? AND year = ? AND month = ? AND day = ?
            LIMIT 1
        ''', (schedule_data['user_id'], schedule_data['year'], 
              schedule_data['month'], schedule_data['day']))
        
        session_row = cursor.fetchone()
        if session_row:
            cursor.execute('''
                UPDATE work_journal_entries
                SET shift_id = ?
                WHERE old_shift_id = ?
            ''', (session_row['id'], old_shift_id))
            updated_count += cursor.rowcount
    
    # Удаляем временную колонку
    try:
        # SQLite не поддерживает DROP COLUMN напрямую, создаём новую таблицу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_journal_entries_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                amount REAL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY (shift_id) REFERENCES work_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
        
        cursor.execute('''
            INSERT INTO work_journal_entries_new (id, shift_id, kind, amount, note, created_at, user_id)
            SELECT id, shift_id, kind, amount, note, created_at, user_id
            FROM work_journal_entries
        ''')
        
        cursor.execute('DROP TABLE work_journal_entries')
        cursor.execute('ALTER TABLE work_journal_entries_new RENAME TO work_journal_entries')
        
        # Индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wje_shift ON work_journal_entries(shift_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wje_kind ON work_journal_entries(kind)')
        
        print(f"   ✅ Обновлено записей: {updated_count}")
    except Exception as e:
        print(f"   ⚠️ Ошибка при обновлении work_journal_entries: {e}")
    
    # 5. Обновляем work_journal_shift (если используется)
    print("\n5. Проверка work_journal_shift...")
    try:
        cursor.execute('SELECT COUNT(*) FROM work_journal_shift')
        count = cursor.fetchone()[0]
        print(f"   ⚠️ Таблица work_journal_shift содержит {count} записей")
        print("   Рекомендуется перенести данные в work_sessions")
    except:
        print("   ℹ️ Таблица work_journal_shift не существует или пуста")
    
    conn.commit()
    
    # 6. Финальная статистика
    print("\n=== СТАТИСТИКА МИГРАЦИИ ===")
    cursor.execute('SELECT COUNT(*) FROM work_schedule')
    print(f"work_schedule записей: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM work_sessions')
    print(f"work_sessions записей: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM work_journal_entries')
    print(f"work_journal_entries записей: {cursor.fetchone()[0]}")
    
    print("\n=== МИГРАЦИЯ ЗАВЕРШЕНА ===")
    
    conn.close()


if __name__ == '__main__':
    migrate()
