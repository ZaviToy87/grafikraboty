import sqlite3
conn = sqlite3.connect('schedule.db')
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [t[0] for t in c.fetchall()]
print('Все таблицы:', tables)
for t in ['vk_messages', 'vk_attachments', 'work_journal_shift', 'work_journal_entries', 'salary_adjustments']:
    if t in tables:
        c.execute(f'SELECT COUNT(*) FROM {t}')
        count = c.fetchone()[0]
        print(f'  {t}: {count} записей')
    else:
        print(f'  {t}: отсутствует')
conn.close()