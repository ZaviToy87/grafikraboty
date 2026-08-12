# -*- coding: utf-8 -*-
"""
Импорт товаров из 1С (два Excel файла)
- ШТРИХ КОДЫ НОМЕНКЛАТУР.xlsx
- НОМЕНКЛАТУРА И ЦЕНА.xlsx
Объединение по точному названию номенклатуры
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = 'schedule.db'
EXCEL_DIR = os.path.dirname(os.path.abspath(__file__))

def normalize_name(name):
    """Нормализовать название для сравнения"""
    if not name:
        return ''
    # Убираем лишние пробелы, приводим к нижнему регистру
    name = str(name).strip().lower()
    # Заменяем несколько пробелов на один
    import re
    name = re.sub(r'\s+', ' ', name)
    # Убираем спецсимволы
    name = re.sub(r'[^\w\sа-яё0-9]', '', name)
    return name


def load_products_from_excel(update_existing=True):
    """
    Загрузить товары из Excel файлов 1С
    Объединение по нормализованному названию номенклатуры
    """
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("❌ Установите openpyxl: pip install openpyxl")
        return {'imported': 0, 'updated': 0, 'errors': []}
    
    # Файлы 1С
    barcode_file = os.path.join(EXCEL_DIR, 'ШТРИХ КОДЫ НОМЕНКЛАТУР.xlsx')
    price_file = os.path.join(EXCEL_DIR, 'НОМЕНКЛАТУРА И ЦЕНА.xlsx')
    
    errors = []
    
    if not os.path.exists(barcode_file):
        errors.append(f"Файл не найден: {barcode_file}")
        return {'imported': 0, 'updated': 0, 'errors': errors}
    
    if not os.path.exists(price_file):
        errors.append(f"Файл не найден: {price_file}")
        return {'imported': 0, 'updated': 0, 'errors': errors}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Шаг 1: Читаем цены → словарь {нормализованное_название: цена}
    # Структура файла: Наименование | Остаток | Картинка | Ед.изм | Картинка | Розничная ₽ | ...
    print("📖 Чтение файла цен...")
    wb_price = load_workbook(price_file, read_only=True, data_only=True)
    ws_price = wb_price.active
    
    price_by_name = {}
    for row_idx, row in enumerate(ws_price.iter_rows(min_row=2), start=2):
        try:
            # Колонка 1 (A) - Наименование
            name = str(row[0].value).strip() if row[0].value else None
            # Колонка 6 (F) - Розничная цена (индекс 5)
            price = float(row[5].value) if row[5] and row[5].value else 0
            # Колонка 8 (H) - Артикул (индекс 7) - ИСПРАВЛЕНО
            vendor_code = str(row[7].value).strip() if row[7] and row[7].value else None
            
            if name and price:
                norm_name = normalize_name(name)
                price_by_name[norm_name] = {
                    'price': price,
                    'group': None,  # Группы нет в этом файле
                    'vendor_code': vendor_code,
                    'original_name': name
                }
        except Exception as e:
            continue
    
    wb_price.close()
    print(f"✅ Прочитано цен: {len(price_by_name)}")
    
    # Шаг 2: Читаем штрих-коды → объединяем с ценами по названию
    print("📖 Чтение файла штрих-кодов...")
    wb_barcode = load_workbook(barcode_file, read_only=True, data_only=True)
    ws_barcode = wb_barcode.active
    
    products = {}
    matched = 0
    
    for row_idx, row in enumerate(ws_barcode.iter_rows(min_row=2), start=2):
        try:
            barcode = str(row[0].value).strip() if row[0].value else None
            name = str(row[1].value).strip() if row[1].value else None
            
            if barcode and name:
                norm_name = normalize_name(name)
                
                # Ищем цену по нормализованному названию
                price_info = price_by_name.get(norm_name)
                
                products[barcode] = {
                    'name': name,
                    'barcode_main': barcode,
                    'retail_price': price_info['price'] if price_info else 0,
                    'group_name': price_info['group'] if price_info else None,
                    'vendor_code': price_info['vendor_code'] if price_info else None,
                    'full_name': name
                }
                
                if price_info:
                    matched += 1
        except Exception as e:
            continue
    
    wb_barcode.close()
    print(f"✅ Прочитано штрих-кодов: {len(products)}")
    print(f"✅ Сопоставлено цен: {matched} ({round(matched/len(products)*100 if products else 0, 1)}%)")
    
    print("💾 Сохранение в базу данных...")
    
    # Сохраняем в базу
    imported = 0
    updated = 0
    
    for barcode, product in products.items():
        try:
            # Проверяем существует ли по штрих-коду
            cursor.execute('SELECT id FROM products_1c WHERE barcode_main = ?', (product.get('barcode_main'),))
            existing = cursor.fetchone()
            
            if existing and update_existing:
                # Обновляем
                cursor.execute('''
                    UPDATE products_1c
                    SET name = ?, full_name = ?, retail_price = ?, group_name = ?, vendor_code = ?, updated_at = ?
                    WHERE barcode_main = ?
                ''', (
                    product.get('name'),
                    product.get('full_name'),
                    product.get('retail_price', 0),
                    product.get('group_name'),
                    product.get('vendor_code'),
                    datetime.now(),
                    product.get('barcode_main')
                ))
                updated += 1
            elif not existing:
                # Добавляем новый
                cursor.execute('''
                    INSERT INTO products_1c
                    (name, full_name, retail_price, barcode_main, group_name, vendor_code, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.get('name'),
                    product.get('full_name'),
                    product.get('retail_price', 0),
                    product.get('barcode_main'),
                    product.get('group_name'),
                    product.get('vendor_code'),
                    datetime.now(),
                    datetime.now()
                ))
                imported += 1
        except Exception as e:
            errors.append(f"{product.get('barcode_main')}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"✅ ИМПОРТ ЗАВЕРШЁН")
    print(f"{'='*50}")
    print(f"📦 Импортировано: {imported}")
    print(f"🔄 Обновлено: {updated}")
    print(f"️ Сопоставлено: {matched}")
    if errors:
        print(f"⚠️ Ошибок: {len(errors)}")
    print(f"{'='*50}\n")
    
    return {'imported': imported, 'updated': updated, 'errors': errors}

if __name__ == '__main__':
    load_products_from_excel()
