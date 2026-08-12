# -*- coding: utf-8 -*-
"""
Создать таблицу products_1c для справочника товаров из 1С
"""
import sqlite3

DB_PATH = 'schedule.db'

def create_products_1c_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products_1c (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Основные данные
            name TEXT NOT NULL,                    -- Наименование
            full_name TEXT,                        -- Полное наименование
            
            -- Цены
            retail_price REAL DEFAULT 0,           -- Розничная цена
            purchase_price REAL DEFAULT 0,         -- Закупочная цена
            
            -- Штрих-коды
            barcode_main TEXT,                     -- Основной штрих-код
            barcode_inner TEXT,                    -- Внутренний штрих-код
            
            -- Группировка
            group_name TEXT,                       -- Группа товаров
            category TEXT,                         -- Категория
            
            -- Единицы измерения
            unit TEXT DEFAULT 'шт',                -- Ед. измерения
            
            -- Метаданные
            vendor_code TEXT,                      -- Артикул
            weight REAL,                           -- Вес
            volume REAL,                           -- Объём
            
            -- Системные поля
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            
            -- Индексы для быстрого поиска
            UNIQUE(barcode_main),
            UNIQUE(barcode_inner)
        )
    ''')
    
    # Индексы для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_1c_barcode ON products_1c(barcode_main)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_1c_name ON products_1c(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_1c_group ON products_1c(group_name)')
    
    conn.commit()
    conn.close()
    print("✅ Таблица products_1c создана успешно!")

if __name__ == '__main__':
    create_products_1c_table()
