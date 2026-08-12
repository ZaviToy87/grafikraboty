import sqlite3
import sys

db = sqlite3.connect('schedule.db')
db.row_factory = sqlite3.Row
c = db.cursor()

# Проверяем, что таблицы существуют и содержат данные
for t in ['sync_sales', 'sync_receipts', 'sync_sale_items', 'sync_receipt_items']:
    c.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'{t}: {c.fetchone()[0]} rows')

# Проверяем структуру sync_sales
c.execute('PRAGMA table_info(sync_sales)')
cols = [r[1] for r in c.fetchall()]
print(f'\nsync_sales columns: {cols}')

# Проверяем структуру sync_receipts
c.execute('PRAGMA table_info(sync_receipts)')
cols = [r[1] for r in c.fetchall()]
print(f'sync_receipts columns: {cols}')

# Проверяем даты
c.execute('SELECT DISTINCT date FROM sync_sales ORDER BY date LIMIT 5')
dates = [r[0] for r in c.fetchall()]
print(f'\nSales dates: {dates}')

c.execute('SELECT DISTINCT date FROM sync_receipts ORDER BY date LIMIT 5')
dates = [r[0] for r in c.fetchall()]
print(f'Receipt dates: {dates}')

db.close()
print('\nDone!')
