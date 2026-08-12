# -*- coding: utf-8 -*-
"""
fix_db_integrity.py — Исправление целостности базы данных
Удаляет записи с нарушенными внешними ключами
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'schedule.db')


def fix_schedule_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы schedule"""
    # Проверяем несуществующие user_id
    cursor.execute('''
        SELECT s.id, s.user_id, u.id as exists_flag
        FROM schedule s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE u.id IS NULL
    ''')
    orphan_schedules = cursor.fetchall()
    print_fn(f"   🗑️  Найдено {len(orphan_schedules)} записей schedule без пользователя")

    for schedule in orphan_schedules:
        print_fn(f"      - Запись id={schedule['id']}, user_id={schedule['user_id']} (пользователь не существует)")
        cursor.execute('DELETE FROM schedule WHERE id = ?', (schedule['id'],))

    # Проверяем записи с task_ids, ссылающимися на несуществующие задачи
    cursor.execute('SELECT id, task_ids FROM schedule')
    all_schedules = cursor.fetchall()
    fixed_count = 0

    for schedule in all_schedules:
        try:
            task_ids = json.loads(schedule['task_ids']) if schedule['task_ids'] else []

            # Проверяем существование задач
            valid_task_ids = []
            for tid in task_ids:
                cursor.execute('SELECT id FROM tasks WHERE id = ?', (tid,))
                if cursor.fetchone():
                    valid_task_ids.append(tid)
                else:
                    print_fn(f"      - Запись id={schedule['id']}: задача {tid} не существует (удалена из списка)")
                    fixed_count += 1

            # Обновляем если есть изменения
            if valid_task_ids != task_ids:
                cursor.execute(
                    'UPDATE schedule SET task_ids = ? WHERE id = ?',
                    (json.dumps(valid_task_ids), schedule['id'])
                )
        except Exception as e:
            print_fn(f"      - Ошибка парсинга task_ids для записи {schedule['id']}: {e}")
            cursor.execute('UPDATE schedule SET task_ids = ? WHERE id = ?', ('[]', schedule['id']))

    if fixed_count > 0:
        print_fn(f"   ✅ Исправлено {fixed_count} ссылок на несуществующие задачи")


def fix_tasks_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы tasks"""
    cursor.execute('''
        SELECT t.id, t.created_by, u.id as exists_flag
        FROM tasks t
        LEFT JOIN users u ON t.created_by = u.id
        WHERE u.id IS NULL AND t.created_by IS NOT NULL
    ''')
    orphan_tasks = cursor.fetchall()
    print_fn(f"   📝 Найдено {len(orphan_tasks)} задач без создателя")

    for task in orphan_tasks:
        print_fn(f"      - Задача id={task['id']}, created_by={task['created_by']} (пользователь не существует)")
        cursor.execute('UPDATE tasks SET created_by = NULL WHERE id = ?', (task['id'],))


def fix_chat_messages_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы chat_messages"""
    cursor.execute('''
        SELECT m.id, m.user_id, u.id as exists_flag
        FROM chat_messages m
        LEFT JOIN users u ON m.user_id = u.id
        WHERE u.id IS NULL
    ''')
    orphan_messages = cursor.fetchall()
    print_fn(f"   💬 Найдено {len(orphan_messages)} сообщений без автора")

    for msg in orphan_messages:
        print_fn(f"      - Сообщение id={msg['id']}, user_id={msg['user_id']} (пользователь не существует)")
        cursor.execute('DELETE FROM chat_messages WHERE id = ?', (msg['id'],))


def fix_files_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы files"""
    cursor.execute('''
        SELECT f.id, f.user_id, u.id as exists_flag
        FROM files f
        LEFT JOIN users u ON f.user_id = u.id
        WHERE u.id IS NULL
    ''')
    orphan_files = cursor.fetchall()
    print_fn(f"   📁 Найдено {len(orphan_files)} файлов без владельца")

    for file in orphan_files:
        print_fn(f"      - Файл id={file['id']}, user_id={file['user_id']} (пользователь не существует)")
        cursor.execute('DELETE FROM files WHERE id = ?', (file['id'],))


def fix_audit_log_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы audit_log"""
    cursor.execute('''
        SELECT a.id, a.user_id, u.id as exists_flag
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE u.id IS NULL
    ''')
    orphan_logs = cursor.fetchall()
    print_fn(f"   📋 Найдено {len(orphan_logs)} записей аудита без пользователя")

    for log in orphan_logs:
        print_fn(f"      - Запись аудита id={log['id']}, user_id={log['user_id']} (пользователь не существует)")
        cursor.execute('DELETE FROM audit_log WHERE id = ?', (log['id'],))


def fix_barcodes_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы barcodes"""
    cursor.execute('''
        SELECT b.id, b.created_by, u.id as exists_flag
        FROM barcodes b
        LEFT JOIN users u ON b.created_by = u.id
        WHERE u.id IS NULL
    ''')
    orphan_barcodes = cursor.fetchall()
    print_fn(f"   📊 Найдено {len(orphan_barcodes)} штрихкодов без создателя")

    for barcode in orphan_barcodes:
        print_fn(f"      - Штрихкод id={barcode['id']}, created_by={barcode['created_by']} (пользователь не существует)")
        cursor.execute('UPDATE barcodes SET created_by = NULL WHERE id = ?', (barcode['id'],))


def fix_sync_sale_items_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы sync_sale_items"""
    # Проверяем несуществующие nomenclature_guid
    cursor.execute('''
        SELECT s.id, s.nomenclature_guid, n.guid as exists_flag
        FROM sync_sale_items s
        LEFT JOIN sync_nomenclature n ON s.nomenclature_guid = n.guid
        WHERE n.guid IS NULL
    ''')
    orphan_items = cursor.fetchall()
    print_fn(f"   🛒 Найдено {len(orphan_items)} записей sync_sale_items без номенклатуры")

    for item in orphan_items:
        print_fn(f"      - Запись id={item['id']}, nomenclature_guid={item['nomenclature_guid']} (номенклатура не существует)")
        cursor.execute('DELETE FROM sync_sale_items WHERE id = ?', (item['id'],))

    # Проверяем несуществующие sale_guid
    cursor.execute('''
        SELECT s.id, s.sale_guid, sl.guid as exists_flag
        FROM sync_sale_items s
        LEFT JOIN sync_sales sl ON s.sale_guid = sl.guid
        WHERE sl.guid IS NULL
    ''')
    orphan_sales = cursor.fetchall()
    print_fn(f"   🛒 Найдено {len(orphan_sales)} записей sync_sale_items без продажи")

    for item in orphan_sales:
        print_fn(f"      - Запись id={item['id']}, sale_guid={item['sale_guid']} (продажа не существует)")
        cursor.execute('DELETE FROM sync_sale_items WHERE id = ?', (item['id'],))


def fix_sync_barcodes_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы sync_barcodes"""
    cursor.execute('''
        SELECT b.id, b.nomenclature_guid, n.guid as exists_flag
        FROM sync_barcodes b
        LEFT JOIN sync_nomenclature n ON b.nomenclature_guid = n.guid
        WHERE n.guid IS NULL
    ''')
    orphan_barcodes = cursor.fetchall()
    print_fn(f"   📊 Найдено {len(orphan_barcodes)} записей sync_barcodes без номенклатуры")

    for barcode in orphan_barcodes:
        print_fn(f"      - Штрихкод id={barcode['id']}, nomenclature_guid={barcode['nomenclature_guid']} (номенклатура не существует)")
        cursor.execute('DELETE FROM sync_barcodes WHERE id = ?', (barcode['id'],))


def fix_sync_receipt_items_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы sync_receipt_items"""
    # Проверяем несуществующие nomenclature_guid
    cursor.execute('''
        SELECT r.id, r.nomenclature_guid, n.guid as exists_flag
        FROM sync_receipt_items r
        LEFT JOIN sync_nomenclature n ON r.nomenclature_guid = n.guid
        WHERE n.guid IS NULL
    ''')
    orphan_items = cursor.fetchall()
    print_fn(f"   📦 Найдено {len(orphan_items)} записей sync_receipt_items без номенклатуры")

    for item in orphan_items:
        print_fn(f"      - Запись id={item['id']}, nomenclature_guid={item['nomenclature_guid']} (номенклатура не существует)")
        cursor.execute('DELETE FROM sync_receipt_items WHERE id = ?', (item['id'],))

    # Проверяем несуществующие receipt_guid
    cursor.execute('''
        SELECT r.id, r.receipt_guid, rc.guid as exists_flag
        FROM sync_receipt_items r
        LEFT JOIN sync_receipts rc ON r.receipt_guid = rc.guid
        WHERE rc.guid IS NULL
    ''')
    orphan_receipts = cursor.fetchall()
    print_fn(f"   📦 Найдено {len(orphan_receipts)} записей sync_receipt_items без поступления")

    for item in orphan_receipts:
        print_fn(f"      - Запись id={item['id']}, receipt_guid={item['receipt_guid']} (поступление не существует)")
        cursor.execute('DELETE FROM sync_receipt_items WHERE id = ?', (item['id'],))


def fix_work_journal_entries_integrity(cursor, print_fn=print):
    """Исправление целостности таблицы work_journal_entries"""
    # Проверяем несуществующие user_id
    cursor.execute('''
        SELECT w.id, w.user_id, u.id as exists_flag
        FROM work_journal_entries w
        LEFT JOIN users u ON w.user_id = u.id
        WHERE u.id IS NULL
    ''')
    orphan_entries = cursor.fetchall()
    print_fn(f"   📓 Найдено {len(orphan_entries)} записей журнала без пользователя")

    for entry in orphan_entries:
        print_fn(f"      - Запись журнала id={entry['id']}, user_id={entry['user_id']} (пользователь не существует)")
        cursor.execute('DELETE FROM work_journal_entries WHERE id = ?', (entry['id'],))

    # Проверяем несуществующие shift_id
    cursor.execute('''
        SELECT w.id, w.shift_id, s.id as exists_flag
        FROM work_journal_entries w
        LEFT JOIN work_journal_shift s ON w.shift_id = s.id
        WHERE s.id IS NULL
    ''')
    orphan_shifts = cursor.fetchall()
    print_fn(f"   📓 Найдено {len(orphan_shifts)} записей журнала без смены")

    for entry in orphan_shifts:
        print_fn(f"      - Запись журнала id={entry['id']}, shift_id={entry['shift_id']} (смена не существует)")
        cursor.execute('DELETE FROM work_journal_entries WHERE id = ?', (entry['id'],))


def print_table_stats(cursor, print_fn=print):
    """Печать статистики таблиц"""
    print_fn("\n📊 Статистика таблиц:")
    tables = ['users', 'tasks', 'schedule', 'files', 'audit_log', 'chat_messages', 'barcodes']
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
            count = cursor.fetchone()['count']
            print_fn(f"   {table}: {count} записей")
        except Exception as e:
            print_fn(f"   {table}: ошибка ({e})")


def fix_integrity():
    """Исправление целостности БД"""
    print("=" * 60)
    print("ПРОВЕРКА И ИСПРАВЛЕНИЕ ЦЕЛОСТНОСТИ БД")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Включаем проверку внешних ключей
    cursor.execute('PRAGMA foreign_keys = ON')

    # Проверяем целостность
    print("\n🔍 Проверка внешних ключей...")
    cursor.execute('PRAGMA foreign_key_check')
    issues = cursor.fetchall()

    if not issues:
        print("✅ Проблем целостности не обнаружено!")
    else:
        print(f"⚠️  Обнаружено {len(issues)} записей с нарушенной целостностью:")

        # Группируем проблемы по таблицам
        problems = {}
        for issue in issues:
            table = issue[0]
            if table not in problems:
                problems[table] = []
            problems[table].append(issue)

        # Исправляем каждую таблицу
        fixers = {
            'schedule': fix_schedule_integrity,
            'tasks': fix_tasks_integrity,
            'chat_messages': fix_chat_messages_integrity,
            'files': fix_files_integrity,
            'audit_log': fix_audit_log_integrity,
            'barcodes': fix_barcodes_integrity,
            'work_journal_entries': fix_work_journal_entries_integrity,
            'sync_sale_items': fix_sync_sale_items_integrity,
            'sync_barcodes': fix_sync_barcodes_integrity,
            'sync_receipt_items': fix_sync_receipt_items_integrity,
        }

        for table, table_issues in problems.items():
            print(f"\n📁 Таблица {table}: {len(table_issues)} проблем")
            fixer = fixers.get(table)
            if fixer:
                fixer(cursor)
            else:
                print(f"   ⚠️  Нет обработчика для таблицы {table}")

    # Сохраняем изменения
    conn.commit()

    # Повторная проверка
    print("\n🔍 Повторная проверка целостности...")
    cursor.execute('PRAGMA foreign_key_check')
    remaining_issues = cursor.fetchall()

    if remaining_issues:
        print(f"⚠️  Осталось {len(remaining_issues)} проблем (требуется ручное вмешательство)")
    else:
        print("✅ Все проблемы целостности исправлены!")

    print_table_stats(cursor)

    conn.close()

    print("\n" + "=" * 60)
    print("ОПЕРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)

if __name__ == '__main__':
    fix_integrity()
