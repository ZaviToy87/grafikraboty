#!/usr/bin/env python3
"""
Импорт препаратов из официального реестра Россельхознадзора
Формат файла: XLS или CSV с данными о ветеринарных препаратах
"""

import os
import sys
import json
import sqlite3
import pandas as pd
from pathlib import Path

def create_drugs_table(db_path='grafikraboty.db'):
    """Создание таблицы для препаратов в основной базе данных"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создание таблицы препаратов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_name TEXT NOT NULL,
        registration_number TEXT,
        active_substance TEXT,
        manufacturer TEXT,
        dosage_form TEXT,
        release_conditions TEXT,
        concentration TEXT,
        unit TEXT,
        shelf_life_months INTEGER,
        prescription_required BOOLEAN DEFAULT 0,
        indications TEXT,
        contraindications TEXT,
        side_effects TEXT,
        shelf_life_text TEXT,
        storage_conditions TEXT,
        all_data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создание индексов для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugs_trade_name ON drugs(trade_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugs_registration_number ON drugs(registration_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugs_active_substance ON drugs(active_substance)')
    
    conn.commit()
    conn.close()
    print(f"Таблица препаратов создана/проверена в базе данных: {db_path}")

def parse_excel_file(file_path):
    """Парсинг Excel файла с препаратами"""
    try:
        # Чтение Excel файла
        df = pd.read_excel(file_path)
        print(f"Файл загружен: {file_path}")
        print(f"Колонки в файле: {list(df.columns)}")
        print(f"Количество строк: {len(df)}")
        
        # Преобразование данных
        drugs = []
        for _, row in df.iterrows():
            # Сбор всех данных из строки
            drug_data = {}
            
            # Собираем все колонки
            for col in df.columns:
                value = row.get(col)
                if pd.notna(value):
                    drug_data[str(col)] = str(value).strip()
            
            # Определение рецептурного статуса
            prescription_required = False
            release_conditions = ''
            
            # Поиск колонки с условиями отпуска
            for col in df.columns:
                if 'отпуск' in str(col).lower():
                    release_conditions = str(row.get(col, '')).lower()
                    break
            
            if release_conditions:
                if 'рецепт' in release_conditions or 'рецептур' in release_conditions:
                    prescription_required = True
                elif 'без рецепта' in release_conditions or 'безрецептур' in release_conditions:
                    prescription_required = False
            
            # Поиск основных полей
            trade_name = ''
            for col in df.columns:
                if 'торгов' in str(col).lower() or 'наименование' in str(col).lower():
                    trade_name = str(row.get(col, '')).strip()
                    break
            
            active_substance = ''
            for col in df.columns:
                if 'международ' in str(col).lower() or 'химическ' in str(col).lower():
                    active_substance = str(row.get(col, '')).strip()
                    break
            
            registration_number = ''
            for col in df.columns:
                if 'регистрац' in str(col).lower() and '№' in str(col):
                    registration_number = str(row.get(col, '')).strip()
                    break
            
            manufacturer = ''
            for col in df.columns:
                if 'производитель' in str(col).lower():
                    manufacturer = str(row.get(col, '')).strip()
                    break
            
            dosage_form = ''
            for col in df.columns:
                if 'форма' in str(col).lower() and 'лекарствен' in str(col).lower():
                    dosage_form = str(row.get(col, '')).strip()
                    break
            
            # Поиск дополнительных полей
            indications = ''
            for col in df.columns:
                if 'показания' in str(col).lower():
                    indications = str(row.get(col, '')).strip()
                    break
            
            contraindications = ''
            for col in df.columns:
                if 'противопоказания' in str(col).lower():
                    contraindications = str(row.get(col, '')).strip()
                    break
            
            side_effects = ''
            for col in df.columns:
                if 'побочные' in str(col).lower():
                    side_effects = str(row.get(col, '')).strip()
                    break
            
            shelf_life = ''
            for col in df.columns:
                if 'срок годности' in str(col).lower():
                    shelf_life = str(row.get(col, '')).strip()
                    break
            
            storage_conditions = ''
            for col in df.columns:
                if 'хранен' in str(col).lower():
                    storage_conditions = str(row.get(col, '')).strip()
                    break
            
            drug = {
                'trade_name': trade_name,
                'registration_number': registration_number,
                'active_substance': active_substance,
                'manufacturer': manufacturer,
                'dosage_form': dosage_form,
                'release_conditions': release_conditions,
                'concentration': '',
                'unit': '',
                'shelf_life_months': 24,
                'prescription_required': prescription_required,
                'indications': indications,
                'contraindications': contraindications,
                'side_effects': side_effects,
                'shelf_life_text': shelf_life,
                'storage_conditions': storage_conditions,
                'all_data': drug_data  # Сохраняем все данные
            }
            
            # Извлечение концентрации из названия
            trade_name_lower = trade_name.lower()
            if 'мг' in trade_name_lower:
                drug['unit'] = 'мг'
            elif 'мл' in trade_name_lower:
                drug['unit'] = 'мл'
            elif 'г' in trade_name_lower:
                drug['unit'] = 'г'
            elif 'мкг' in trade_name_lower:
                drug['unit'] = 'мкг'
            
            # Пропускаем пустые записи
            if trade_name and active_substance:
                drugs.append(drug)
        
        print(f"Извлечено препаратов: {len(drugs)}")
        return drugs
    
    except Exception as e:
        print(f"Ошибка при парсинге файла: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_csv_file(file_path):
    """Парсинг CSV файла с препаратами"""
    try:
        # Чтение CSV файла
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"Файл загружен: {file_path}")
        print(f"Колонки в файле: {list(df.columns)}")
        print(f"Количество строк: {len(df)}")
        
        # Преобразование данных
        drugs = []
        for _, row in df.iterrows():
            # Определение рецептурного статуса
            prescription_required = False
            release_conditions = str(row.get('Условия отпуска', '')).lower() if 'Условия отпуска' in df.columns else ''
            
            if release_conditions:
                if 'рецепт' in release_conditions or 'рецептур' in release_conditions:
                    prescription_required = True
                elif 'без рецепта' in release_conditions or 'безрецептур' in release_conditions:
                    prescription_required = False
            
            drug = {
                'trade_name': str(row.get('Торговое наименование', '')).strip(),
                'registration_number': str(row.get('Регистрационный номер', '')).strip(),
                'active_substance': str(row.get('Международное непатентованное наименование', '')).strip(),
                'manufacturer': str(row.get('Наименование производителя', '')).strip(),
                'dosage_form': str(row.get('Лекарственная форма', '')).strip(),
                'release_conditions': release_conditions,
                'concentration': '',
                'unit': '',
                'shelf_life_months': 24,
                'prescription_required': prescription_required
            }
            
            drugs.append(drug)
        
        return drugs
    
    except Exception as e:
        print(f"Ошибка при парсинге файла: {e}")
        return []

def save_drugs_to_db(drugs, db_path='grafikraboty.db'):
    """Сохранение препаратов в базу данных"""
    if not drugs:
        print("Нет данных для сохранения")
        return 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    for drug in drugs:
        try:
            # Преобразование всех данных в JSON
            all_data_json = json.dumps(drug.get('all_data', {}), ensure_ascii=False)
            
            # Проверка существования препарата
            cursor.execute(
                'SELECT id FROM drugs WHERE registration_number = ? OR trade_name = ?',
                (drug['registration_number'], drug['trade_name'])
            )
            existing = cursor.fetchone()
            
            if existing:
                # Обновление существующего препарата
                cursor.execute('''
                UPDATE drugs SET
                    trade_name = ?,
                    active_substance = ?,
                    manufacturer = ?,
                    dosage_form = ?,
                    release_conditions = ?,
                    concentration = ?,
                    unit = ?,
                    shelf_life_months = ?,
                    prescription_required = ?,
                    indications = ?,
                    contraindications = ?,
                    side_effects = ?,
                    shelf_life_text = ?,
                    storage_conditions = ?,
                    all_data_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (
                    drug['trade_name'],
                    drug['active_substance'],
                    drug['manufacturer'],
                    drug['dosage_form'],
                    drug['release_conditions'],
                    drug['concentration'],
                    drug['unit'],
                    drug['shelf_life_months'],
                    1 if drug['prescription_required'] else 0,
                    drug.get('indications', ''),
                    drug.get('contraindications', ''),
                    drug.get('side_effects', ''),
                    drug.get('shelf_life_text', ''),
                    drug.get('storage_conditions', ''),
                    all_data_json,
                    existing[0]
                ))
            else:
                # Вставка нового препарата
                cursor.execute('''
                INSERT INTO drugs (
                    trade_name, registration_number, active_substance,
                    manufacturer, dosage_form, release_conditions,
                    concentration, unit, shelf_life_months, prescription_required,
                    indications, contraindications, side_effects,
                    shelf_life_text, storage_conditions, all_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    drug['trade_name'],
                    drug['registration_number'],
                    drug['active_substance'],
                    drug['manufacturer'],
                    drug['dosage_form'],
                    drug['release_conditions'],
                    drug['concentration'],
                    drug['unit'],
                    drug['shelf_life_months'],
                    1 if drug['prescription_required'] else 0,
                    drug.get('indications', ''),
                    drug.get('contraindications', ''),
                    drug.get('side_effects', ''),
                    drug.get('shelf_life_text', ''),
                    drug.get('storage_conditions', ''),
                    all_data_json
                ))
                inserted_count += 1
        
        except Exception as e:
            print(f"Ошибка при сохранении препарата {drug['trade_name']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"Сохранено препаратов: {inserted_count}")
    return inserted_count

def export_drugs_to_json(db_path='grafikraboty.db', output_path='static/data/drugs.json'):
    """Экспорт препаратов в JSON для использования на фронтенде"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        trade_name, registration_number, active_substance,
        manufacturer, dosage_form, release_conditions,
        concentration, unit, shelf_life_months, prescription_required,
        indications, contraindications, side_effects,
        shelf_life_text, storage_conditions, all_data_json
    FROM drugs
    ORDER BY trade_name
    ''')
    
    drugs = []
    for row in cursor.fetchall():
        # Парсинг всех данных из JSON
        all_data = {}
        if row[15]:
            try:
                all_data = json.loads(row[15])
            except:
                all_data = {}
        
        drug = {
            'name': row[0],
            'registrationNumber': row[1],
            'activeSubstance': row[2],
            'manufacturer': row[3],
            'form': row[4],
            'releaseConditions': row[5],
            'concentration': row[6],
            'unit': row[7],
            'shelfLife': row[8],
            'prescriptionRequired': bool(row[9]),
            'indications': row[10],
            'contraindications': row[11],
            'sideEffects': row[12],
            'shelfLifeText': row[13],
            'storageConditions': row[14],
            'allData': all_data
        }
        drugs.append(drug)
    
    conn.close()
    
    # Создание директории, если не существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Сохранение в JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=2)
    
    print(f"Экспортировано {len(drugs)} препаратов в {output_path}")
    return len(drugs)

def main():
    """Основная функция"""
    print("=== Импорт препаратов из реестра Россельхознадзора ===")
    
    # Создание таблицы препаратов
    create_drugs_table()
    
    # Проверка аргументов командной строки
    if len(sys.argv) < 2:
        print("Использование: python import_drugs_from_excel.py <путь_к_файлу>")
        print("Поддерживаемые форматы: .xls, .xlsx, .csv")
        return
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        return
    
    # Определение типа файла и парсинг
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext in ['.xls', '.xlsx']:
        drugs = parse_excel_file(file_path)
    elif file_ext == '.csv':
        drugs = parse_csv_file(file_path)
    else:
        print(f"Неподдерживаемый формат файла: {file_ext}")
        return
    
    if not drugs:
        print("Не удалось извлечь данные из файла")
        return
    
    # Сохранение в базу данных
    saved_count = save_drugs_to_db(drugs)
    
    # Экспорт в JSON для фронтенда
    export_drugs_to_json()
    
    print(f"\n=== Импорт завершен ===")
    print(f"Обработано препаратов: {len(drugs)}")
    print(f"Сохранено в базу данных: {saved_count}")
    print(f"Файл для фронтенда: static/data/drugs.json")

if __name__ == '__main__':
    main()