# -*- coding: utf-8 -*-
"""
update_prices_from_excel.py — Обновление цен в базе products_1c из Excel файла
"""
import sqlite3
from openpyxl import load_workbook
import os
import re

DB_PATH = 'schedule.db'
EXCEL_FILE = 'НОМЕНКЛАТУРА И ЦЕНА.xlsx'

def normalize_name(name):
    """Нормализовать название для сравнения"""
    if not name:
        return ''
    # Убираем лишние пробелы, приводим к нижнему регистру
    name = str(name).strip().lower()
    # Заменяем несколько пробелов на один
    name = re.sub(r'\s+', ' ', name)
    # Убираем спецсимволы
    name = re.sub(r'[^\w\sа-яё0-9]', '', name)
    return name

def update_prices():
    print("=" * 70)
    print("🔄 ОБНОВЛЕНИЕ ЦЕН В БАЗЕ products_1c")
    print("=" * 70)
    
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCEL_FILE)
    
    if not os.path.exists(excel_path):
        print(f"❌ Файл не найден: {excel_path}")
        return
    
    print(f"📖 Чтение файла: {EXCEL_FILE}")
    wb = load_workbook(excel_path, data_only=True)
    ws = wb.active
    
    price_by_name = {}
    for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
        # Пропускаем заголовок
        if row_idx == 1:
            continue
            
        # A - Наименование, F - розничная цена
        name = str(row[0]).strip() if row[0] else None
        price = float(row[5]) if len(row) > 5 and row[5] else 0
        
        if name and price:
            norm_name = normalize_name(name)
            price_by_name[norm_name] = {
                'price': price,
                'original_name': name
            }
    
    wb.close()
    print(f"✅ Прочитано цен из Excel: {len(price_by_name)}")
    
    # Подключаемся к базе
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products_1c')
    total_products = cursor.fetchone()[0]
    print(f"📦 Товаров в базе: {total_products}")
    
    cursor.execute('SELECT COUNT(*) FROM products_1c WHERE retail_price > 0')
    with_prices = cursor.fetchone()[0]
    print(f"✅ Товаров с ценой сейчас: {with_prices}")
    
    # Обновляем цены
    updated = 0
    not_found = 0
    
    print("\n🔄 Обновление цен...")
    cursor.execute('SELECT id, name, retail_price FROM products_1c')
    for prod_id, name, current_price in cursor.fetchall():
        norm_name = normalize_name(name)
        price_info = price_by_name.get(norm_name)
        
        if price_info and price_info['price'] > 0:
            new_price = price_info['price']
            # Обновляем только если цена отличается
            if current_price != new_price:
                cursor.execute('''
                    UPDATE products_1c
                    SET retail_price = ?, updated_at = datetime('now')
                    WHERE id = ?
                ''', (new_price, prod_id))
                updated += 1
                
                if updated <= 10:
                    print(f"  ✅ {name[:50]}: {current_price} → {new_price} ₽")
        else:
            not_found += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n{'=' * 70}")
    print(f"✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
    print(f"{'=' * 70}")
    print(f"📦 Всего товаров: {total_products}")
    print(f"🔄 Обновлено цен: {updated}")
    print(f"❌ Не найдено совпадений: {not_found}")
    print(f"✅ Товаров с ценой: {with_prices + updated}")
    print(f"{'=' * 70}")

if __name__ == '__main__':
    update_prices()
