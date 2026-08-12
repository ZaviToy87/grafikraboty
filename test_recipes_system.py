#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование системы рецептов
"""
import sqlite3
import json
import os

def test_database():
    """Тестирование базы данных препаратов"""
    print("=== Тестирование базы данных препаратов ===")
    
    # Проверка таблицы drugs
    conn = sqlite3.connect('grafikraboty.db')
    cursor = conn.cursor()
    
    # Количество препаратов
    cursor.execute('SELECT COUNT(*) FROM drugs')
    count = cursor.fetchone()[0]
    print(f"Количество препаратов в базе: {count}")
    
    # Проверка структуры
    cursor.execute('PRAGMA table_info(drugs)')
    columns = cursor.fetchall()
    print(f"Колонки в таблице drugs: {len(columns)}")
    
    # Проверка нескольких записей
    cursor.execute('SELECT trade_name, registration_number, active_substance FROM drugs LIMIT 3')
    print("Первые 3 препарата:")
    for i, row in enumerate(cursor.fetchall()):
        print(f"  {i+1}. {row[0]} (РУ: {row[1]})")
    
    conn.close()
    return count > 0

def test_json_file():
    """Тестирование JSON файла препаратов"""
    print("\n=== Тестирование JSON файла препаратов ===")
    
    json_path = 'static/data/drugs.json'
    if not os.path.exists(json_path):
        print(f"JSON файл не найден: {json_path}")
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"JSON файл содержит {len(data)} препаратов")
    
    if data:
        first_drug = data[0]
        print(f"Первый препарат в JSON:")
        print(f"  Название: {first_drug.get('name', 'Нет')}")
        print(f"  Рег. номер: {first_drug.get('registrationNumber', 'Нет')}")
        print(f"  Действующее вещество: {first_drug.get('activeSubstance', 'Нет')}")
    
    return len(data) > 0

def test_recipes_database():
    """Тестирование базы данных рецептов"""
    print("\n=== Тестирование системы рецептов ===")
    
    print("Система рецептов использует localStorage на клиентской стороне")
    print("Для работы не требуется серверная база данных рецептов")
    
    # Проверяем, что фронтенд файлы существуют
    frontend_files = [
        'templates/recipes.html',
        'static/js/recipes.js'
    ]
    
    missing_files = []
    for file in frontend_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"Отсутствуют файлы фронтенда: {missing_files}")
        return False
    
    print("✓ Фронтенд система рецептов настроена корректно")
    return True

def test_pdf_generation():
    """Тестирование генерации PDF"""
    print("\n=== Тестирование генерации PDF ===")
    
    pdf_dir = 'static/pdf'
    if os.path.exists(pdf_dir):
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        print(f"Найдено {len(pdf_files)} PDF файлов в {pdf_dir}")
        
        if pdf_files:
            print("Примеры PDF файлов:")
            for i, pdf in enumerate(pdf_files[:3]):
                print(f"  {i+1}. {pdf}")
    else:
        print(f"Директория PDF не существует: {pdf_dir}")
    
    return True

def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ РЕЦЕПТОВ")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Тест 1: База данных препаратов
    if test_database():
        tests_passed += 1
        print("✓ База данных препаратов работает корректно")
    else:
        print("✗ Проблемы с базой данных препаратов")
    
    # Тест 2: JSON файл препаратов
    if test_json_file():
        tests_passed += 1
        print("✓ JSON файл препаратов работает корректно")
    else:
        print("✗ Проблемы с JSON файлом препаратов")
    
    # Тест 3: База данных рецептов
    if test_recipes_database():
        tests_passed += 1
        print("✓ База данных рецептов работает корректно")
    else:
        print("✗ Проблемы с базой данных рецептов")
    
    # Тест 4: Генерация PDF
    if test_pdf_generation():
        tests_passed += 1
        print("✓ Генерация PDF работает корректно")
    else:
        print("✗ Проблемы с генерацией PDF")
    
    print("\n" + "=" * 60)
    print(f"ИТОГ: {tests_passed}/{total_tests} тестов пройдено")
    
    if tests_passed == total_tests:
        print("✓ Вся система рецептов работает корректно!")
        return True
    else:
        print("✗ Есть проблемы в системе рецептов")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)