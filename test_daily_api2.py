import sqlite3
import json

db = sqlite3.connect('schedule.db')
c = db.cursor()

# Продажи по дням
c.execute('''
    SELECT 
        date,
        COUNT(*) as doc_count,
        COALESCE(SUM(total_sum), 0) as total_sum
    FROM sync_sales
    GROUP BY date
    ORDER BY date ASC
''')

sales_by_day = {}
for row in c.fetchall():
    sales_by_day[row[0]] = {
        'doc_count': row[1],
        'total_sum': float(row[2])
    }

print(f"Sales days: {len(sales_by_day)}")
for d, v in sorted(sales_by_day.items())[:5]:
    print(f"  {d}: docs={v['doc_count']}, sum={v['total_sum']}")

# Приемки по дням
c.execute('''
    SELECT 
        date,
        COUNT(*) as doc_count,
        COALESCE(SUM(total_sum), 0) as total_sum
    FROM sync_receipts
    GROUP BY date
    ORDER BY date ASC
''')

receipts_by_day = {}
for row in c.fetchall():
    receipts_by_day[row[0]] = {
        'doc_count': row[1],
        'total_sum': float(row[2])
    }

print(f"\nReceipts days: {len(receipts_by_day)}")
for d, v in sorted(receipts_by_day.items())[:5]:
    print(f"  {d}: docs={v['doc_count']}, sum={v['total_sum']}")

# Собираем все даты
all_dates = sorted(set(list(sales_by_day.keys()) + list(receipts_by_day.keys())))
print(f"\nTotal unique dates: {len(all_dates)}")

# Формируем daily_data
daily_data = []
for date in all_dates:
    s = sales_by_day.get(date, {})
    r = receipts_by_day.get(date, {})
    daily_data.append({
        'date': date,
        'sales': {
            'doc_count': s.get('doc_count', 0),
            'total_sum': s.get('total_sum', 0)
        },
        'receipts': {
            'doc_count': r.get('doc_count', 0),
            'total_sum': r.get('total_sum', 0)
        }
    })

print(f"\nDaily data count: {len(daily_data)}")
print(f"First 3 days: {json.dumps(daily_data[:3], ensure_ascii=False, indent=2)}")

# Итоги
total_sales_sum = sum(d['sales']['total_sum'] for d in daily_data)
total_receipts_sum = sum(d['receipts']['total_sum'] for d in daily_data)
print(f"\nTotal sales sum: {total_sales_sum}")
print(f"Total receipts sum: {total_receipts_sum}")

db.close()
print("\nSUCCESS!")
