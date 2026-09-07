#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Потоковый анализ XML-выгрузки из 1С (без загрузки всего файла в память)
"""

import os
import re
from collections import Counter

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)
print(f"Размер файла: {filesize:,} байт ({filesize/1024/1024:.2f} MB)")

# Читаем файл блоками по 1MB
print("\nАнализируем структуру...")

# Сначала найдем позицию Body
with open(filepath, 'r', encoding='utf-8') as f:
    # Ищем <Body> и </Body> в первых 100KB
    chunk = f.read(100000)
    body_start = chunk.find('<Body>')
    body_end = chunk.find('</Body>')
    print(f"<Body> на позиции: {body_start}")
    print(f"</Body> на позиции: {body_end}")
    
    if body_start == -1:
        # Ищем msg:Body
        body_start = chunk.find('<msg:Body>')
        body_end = chunk.find('</msg:Body>')
        print(f"<msg:Body> на позиции: {body_start}")
        print(f"</msg:Body> на позиции: {body_end}")

# Теперь проанализируем структуру Body, читая его частями
print("\n\n=== АНАЛИЗ ОБЪЕКТОВ В ФАЙЛЕ ===")

# Используем итеративный подход - ищем все теги с точкой
# Читаем файл кусками
object_counts = Counter()
current_objects = {}  # Для отслеживания вложенности

with open(filepath, 'r', encoding='utf-8') as f:
    # Пропускаем Header
    while True:
        line = f.readline()
        if not line:
            break
        if '<Body' in line or '<msg:Body>' in line:
            break
    
    print("Начало Body найдено, анализируем...")
    
    # Читаем Body построчно
    body_content = []
    line_count = 0
    while True:
        line = f.readline()
        if not line or '</Body>' in line or '</msg:Body>' in line:
            break
        body_content.append(line)
        line_count += 1
        
        if line_count % 100000 == 0:
            print(f"  Прочитано {line_count} строк...")
    
    body_text = ''.join(body_content)
    print(f"Body: {len(body_text)} символов, {line_count} строк")

# Анализируем объекты
print("\n\n=== ОБЪЕКТЫ МЕТАДАННЫХ ===")
# Ищем теги вида Справочник.XXX, Документ.XXX, РегистрНакопления.XXX и т.д.
obj_tags = re.findall(r'<(\w+\.\w+)', body_text)
obj_counter = Counter(obj_tags)

print(f"Всего типов объектов: {len(obj_counter)}")
for tag, count in obj_counter.most_common():
    print(f"  {tag}: {count}")

# Для каждого типа покажем структуру
print("\n\n=== СТРУКТУРА ОБЪЕКТОВ ===")
for obj_type, count in obj_counter.most_common():
    # Найдем первый блок
    pattern = f'<{obj_type}[^>]*>(.*?)</{obj_type}>'
    match = re.search(pattern, body_text, re.DOTALL)
    if match:
        block = match.group(1)
        inner_tags = set(re.findall(r'<(\w+)>', block))
        print(f"\n--- {obj_type} (всего: {count}) ---")
        print(f"  Поля: {', '.join(sorted(inner_tags))}")
        # Покажем первые 200 символов
        print(f"  Пример: {block[:200]}...")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
