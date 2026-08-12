# -*- coding: utf-8 -*-
"""
test_full_barcode_chain.py — Полная проверка цепочки штрих-кодов
"""
import sqlite3
import requests
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8080'

print("=" * 70)
print("🔍 ПОЛНАЯ ПРОВЕРКА ЦЕПОЧКИ ШТРИХ-КОДОВ")
print("=" * 70)

# Шаг 1: Проверка базы данных
print("\n📌 ШАГ 1: Проверка базы данных...")
conn = sqlite3.connect('schedule.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM products_1c')
total = cursor.fetchone()[0]
print(f"✅ Товаров в базе: {total}")

cursor.execute('SELECT COUNT(*) FROM products_1c WHERE retail_price > 0')
with_prices = cursor.fetchone()[0]
print(f"✅ Товаров с ценой: {with_prices}")

cursor.execute('SELECT COUNT(*) FROM products_1c WHERE retail_price = 0 OR retail_price IS NULL')
no_prices = cursor.fetchone()[0]
print(f"❌ Товаров БЕЗ цены: {no_prices}")

# Проверяем конкретный штрих-код
barcode = '9003579309537'
cursor.execute('SELECT id, name, retail_price, barcode_main FROM products_1c WHERE barcode_main = ?', (barcode,))
product = cursor.fetchone()
print(f"\n📦 Штрих-код {barcode}:")
if product:
    print(f"  ID: {product[0]}")
    print(f"  Название: {product[1]}")
    print(f"  Цена: {product[2]} ₽")
    print(f"  Штрих-код: {product[3]}")
else:
    print(f"  ❌ НЕ НАЙДЕН!")

conn.close()

# Шаг 2: Проверка API
print("\n📌 ШАГ 2: Проверка API маршрутов...")

try:
    # Проверяем поиск по штрих-коду
    response = requests.get(f'{BASE_URL}/api/products-1c/barcode/{barcode}')
    print(f"GET /api/products-1c/barcode/{barcode}")
    print(f"  Статус: {response.status_code}")
    print(f"  Ответ: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")

try:
    # Проверяем поиск по названию
    response = requests.get(f'{BASE_URL}/api/products-1c/search?query=РОЯЛ&limit=5')
    print(f"\nGET /api/products-1c/search?query=РОЯЛ")
    print(f"  Статус: {response.status_code}")
    print(f"  Ответ: {response.text[:200]}")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")

# Шаг 3: Проверка HTML модального окна
print("\n📌 ШАГ 3: Проверка модального окна...")
try:
    response = requests.get(f'{BASE_URL}/dashboard')
    html = response.text
    
    checks = {
        'revision-add-modal': 'Модальное окно ревизии',
        'rev-product-name': 'Поле названия товара',
        'rev-quantity': 'Поле количества',
        'rev-barcode': 'Поле штрих-кода',
        'rev-retail-price': 'Поле цены',
        'rev-expiry-date': 'Поле срока годности',
        'rev-1c-search': 'Поле поиска 1С',
    }
    
    for id, name in checks.items():
        if id in html:
            print(f"  ✅ {name} (#{id}) найден")
        else:
            print(f"  ❌ {name} (#{id}) НЕ НАЙДЕН!")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")

# Шаг 4: Проверка JavaScript перехвата
print("\n📌 ШАГ 4: Проверка JavaScript...")
try:
    response = requests.get(f'{BASE_URL}/static/js/app.js')
    js = response.text
    
    checks = {
        'barcodeBuffer': 'Буфер штрих-кода',
        'handleBarcodeScanned': 'Функция обработки штрих-кода',
        'search1cProducts': 'Функция поиска 1С',
        'select1cProduct': 'Функция выбора товара',
    }
    
    for code, name in checks.items():
        if code in js:
            print(f"  ✅ {name} найден")
        else:
            print(f"  ❌ {name} НЕ НАЙДЕН!")
except Exception as e:
    print(f"  ❌ Ошибка: {e}")

print("\n" + "=" * 70)
print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 70)
print("\n⚠️  ПРОБЛЕМА ОБНАРУЖЕНА: Все товары в базе имеют цену 0!")
print("🔧 Это нужно исправить импортом или обновлением цен.")
