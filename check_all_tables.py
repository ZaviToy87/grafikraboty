# -*- coding: utf-8 -*-
"""
check_all_tables.py - Полная проверка всех таблиц БД
"""
import sqlite3

conn = sqlite3.connect('schedule.db')
c = conn.cursor()

print('='*60)
print(' ПРОВЕРКА ВСЕХ ТАБЛИЦ В БАЗЕ ДАННЫХ')
print('='*60)

# Все таблицы
c.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = [t[0] for t in c.fetchall()]
print(f'\nВсего таблиц: {len(tables)}')
for t in tables:
    c.execute(f'SELECT COUNT(*) FROM {t}')
    count = c.fetchone()[0]
    status = '✅' if count > 0 else '⚠️  ПУСТО'
    print(f'  {status} {t}: {count} записей')

print('\n' + '='*60)
print(' ДЕТАЛЬНАЯ ИНФОРМАЦИЯ')
print('='*60)

# 1. Сотрудники
print('\n📊 1. СОТРУДНИКИ (users):')
c.execute('SELECT id, username, role, full_name FROM users')
for row in c.fetchall():
    print(f'  ID={row[0]}, {row[1]} ({row[2]}): {row[3]}')

# 2. Задачи
print('\n📊 2. ЗАДАЧИ (tasks):')
c.execute('SELECT id, name, color FROM tasks')
for row in c.fetchall():
    print(f'  ID={row[0]}: {row[1]} ({row[2]})')

# 3. График смен
print('\n📊 3. ГРАФИК СМЕН (schedule):')
c.execute('SELECT COUNT(*) FROM schedule')
total = c.fetchone()[0]
print(f'  Всего записей: {total}')

c.execute('SELECT COUNT(*) FROM schedule WHERE task_ids LIKE "%6%"')
shifts = c.fetchone()[0]
print(f'  Из них смен физических (task_id=6): {shifts}')

print('\n  Последние 10 записей:')
c.execute('SELECT id, user_id, year, month, day, task_ids FROM schedule ORDER BY id DESC LIMIT 10')
for row in c.fetchall():
    print(f'    ID={row[0]}, user_id={row[1]}, {row[2]}.{row[3]}.{row[4]}, task_ids={row[5]}')

# 4. Рабочий журнал - записи
print('\n📊 4. РАБОЧИЙ ЖУРНАЛ - записи (work_journal_entries):')
c.execute('SELECT COUNT(*) FROM work_journal_entries')
total = c.fetchone()[0]
print(f'  Всего записей: {total}')

if total > 0:
    c.execute('SELECT kind, COUNT(*) FROM work_journal_entries GROUP BY kind')
    for row in c.fetchall():
        print(f'    {row[0]}: {row[1]}')

# 5. Рабочий журнал - смены
print('\n📊 5. РАБОЧИЙ ЖУРНАЛ - смены (work_journal_shift):')
c.execute('SELECT COUNT(*) FROM work_journal_shift')
total = c.fetchone()[0]
print(f'  Всего смен: {total}')

# 6. Чат - темы
print('\n📊 6. ЧАТ - темы (chat_topics):')
c.execute('SELECT id, title FROM chat_topics')
for row in c.fetchall():
    print(f'  ID={row[0]}: {row[1]}')

# 7. Чат - сообщения
print('\n📊 7. ЧАТ - сообщения (chat_messages):')
c.execute('SELECT COUNT(*) FROM chat_messages')
total = c.fetchone()[0]
print(f'  Всего сообщений: {total}')

# 8. Файлы
print('\n📊 8. ФАЙЛЫ (files):')
c.execute('SELECT COUNT(*) FROM files')
total = c.fetchone()[0]
print(f'  Всего файлов: {total}')
if total > 0:
    c.execute('SELECT id, filename, uploaded_at FROM files ORDER BY id DESC LIMIT 5')
    for row in c.fetchall():
        print(f'    ID={row[0]}, {row[1]} ({row[2]})')

# 9. Штрих-коды
print('\n📊 9. ШТРИХ-КОДЫ (barcodes):')
c.execute('SELECT COUNT(*) FROM barcodes')
total = c.fetchone()[0]
print(f'  Всего штрих-кодов: {total}')

# 10. Аудит лог
print('\n📊 10. АУДИТ ЛОГ (audit_log):')
c.execute('SELECT COUNT(*) FROM audit_log')
total = c.fetchone()[0]
print(f'  Всего записей: {total}')

# 11. Штрафы/бонусы
print('\n📊 11. ШТРАФЫ/БОНУСЫ (salary_adjustments):')
c.execute('SELECT COUNT(*) FROM salary_adjustments')
total = c.fetchone()[0]
print(f'  Всего записей: {total}')

# 12. Задачи коллег
print('\n📊 12. ЗАДАЧИ КОЛЛЕГ (colleague_tasks):')
c.execute('SELECT COUNT(*) FROM colleague_tasks')
total = c.fetchone()[0]
print(f'  Всего записей: {total}')

print('\n' + '='*60)
print(' ПРОВЕРКА ЗАВЕРШЕНА')
print('='*60)

conn.close()
