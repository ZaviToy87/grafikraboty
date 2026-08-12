# -*- coding: utf-8 -*-
"""
Импорт штрих-кодов из Excel в базу данных
"""
import sqlite3
import openpyxl
import os
import hashlib

# Пути к БД
DB_PATHS = [
    r"C:\Users\User\Desktop\GrafikRaboty\schedule.db",
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GrafikRaboty', 'schedule.db')
]

EXCEL_FILE = r"C:\Users\User\Desktop\Новые штрих кода.1.xlsx"

def import_barcodes_to_db(db_path, barcodes_data):
    """Импортировать штрих-коды в базу данных."""
    if not os.path.exists(db_path):
        print(f"  ⚠️  БД не найдена: {db_path}")
        return 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем ID администратора (user_id=1)
    admin_id = 1
    
    imported = 0
    for row in barcodes_data:
        product_name = row[0] if len(row) > 0 else ""
        factory_barcode = str(row[1]) if len(row) > 1 and row[1] else ""
        internal_barcode = str(row[2]) if len(row) > 2 and row[2] else ""
        
        if not product_name:
            continue
        
        # Проверяем, есть ли уже такой штрих-код
        cursor.execute('SELECT id FROM barcodes WHERE internal_barcode = ?', (internal_barcode,))
        if cursor.fetchone():
            continue  # Уже есть
        
        # Добавляем
        cursor.execute('''
            INSERT OR IGNORE INTO barcodes (product_name, factory_barcode, internal_barcode, created_by)
            VALUES (?, ?, ?, ?)
        ''', (product_name, factory_barcode, internal_barcode, admin_id))
        
        if cursor.rowcount > 0:
            imported += 1
    
    conn.commit()
    conn.close()
    return imported

if __name__ == "__main__":
    print("=" * 60)
    print("ИМПОРТ ШТРИХ-КОДОВ ИЗ EXCEL")
    print("=" * 60)
    
    # Читаем Excel
    print(f"\nЧтение файла: {EXCEL_FILE}")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # Пропускаем заголовок, берём данные
    data = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:  # Есть наименование
            data.append(row)
    
    print(f"Найдено строк: {len(data)}")
    
    # Импортируем в каждую БД
    for db_path in DB_PATHS:
        print(f"\nИмпорт в БД: {db_path}")
        count = import_barcodes_to_db(db_path, data)
        print(f"  ✅ Импортировано: {count}")
    
    print("\n" + "=" * 60)
    print("ИМПОРТ ЗАВЕРШЁН!")
    print("=" * 60)
    
    # Проверяем результат
    for db_path in DB_PATHS:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM barcodes')
            count = cursor.fetchone()[0]
            cursor.execute('SELECT product_name, factory_barcode, internal_barcode FROM barcodes LIMIT 3')
            samples = cursor.fetchall()
            conn.close()
            print(f"\n{db_path}:")
            print(f"  Всего штрих-кодов: {count}")
            print(f"  Примеры:")
            for s in samples:
                print(f"    - {s[0][:40]}... | {s[1]} | {s[2]}")
