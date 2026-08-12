#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Глубокий анализ структуры XML-выгрузки из 1С
"""

import os
import re

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'

print("Читаем файл...")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Размер: {len(content)} символов")

# Ищем все теги с их содержимым (первые 5000 символов)
print("\n=== ПЕРВЫЕ 3000 СИМВОЛОВ ===")
print(content[:3000])

# Ищем закрывающие теги
print("\n\n=== ПОСЛЕДНИЕ 1000 СИМВОЛОВ ===")
print(content[-1000:])

# Ищем все XML-теги с их позициями
print("\n\n=== ВСЕ ТЕГИ В ФАЙЛЕ (уникальные) ===")
all_tags = set(re.findall(r'</?(\w+(?::\w+)?)[>\s]', content))
for tag in sorted(all_tags):
    print(f"  <{tag}>")

# Ищем содержимое между тегами
print("\n\n=== ПОИСК КОНКРЕТНЫХ ДАННЫХ ===")

# Ищем все, что похоже на данные (не теги)
# Найдем блоки текста между тегами
text_blocks = re.findall(r'>([^<]+)<', content)
# Отфильтруем только осмысленные тексты (не пустые, не пробелы)
meaningful = [t.strip() for t in text_blocks if t.strip() and len(t.strip()) > 3]
print(f"Осмысленных текстовых блоков: {len(meaningful)}")
if meaningful:
    print("Первые 30:")
    for m in meaningful[:30]:
        print(f"  {m}")

# Ищем GUID
guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', content)
print(f"\nGUID: {len(guids)}")
if guids:
    print(f"  Первые 5: {guids[:5]}")

# Ищем даты
dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
print(f"\nДат: {len(dates)}")
if dates:
    print(f"  Первые 10: {dates[:10]}")

# Ищем числа с десятичной точкой
nums = re.findall(r'>(\d+\.\d+)<', content)
print(f"\nЧисел с точкой: {len(nums)}")
if nums:
    print(f"  Первые 10: {nums[:10]}")

# Ищем числа целые
ints = re.findall(r'>(\d+)<', content)
print(f"\nЦелых чисел: {len(ints)}")
if ints:
    print(f"  Первые 10: {ints[:10]}")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
