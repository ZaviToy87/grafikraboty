#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Глубокий анализ содержимого Body XML-выгрузки из 1С
"""

import os
import re
from collections import Counter, defaultdict

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'

# Читаем файл частями, чтобы найти все типы объектов в Body
print("Анализируем содержимое Body...")

# Ищем все вхождения <EnterpriseData...> и что внутри
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим Body
body_start = content.find('<msg:Body>')
body_end = content.find('</msg:Body>')
body_content = content[body_start:body_end]

print(f"\nBody размер: {len(body_content)} символов")

# Ищем все корневые элементы внутри Body (EnterpriseData)
# Формат: <EnterpriseData ... xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData">
# Внутри могут быть: Catalog, Document, AccumulationRegister и т.д.

# Найдем все типы объектов верхнего уровня
# Ищем <ИмяТипа> или <ИмяТипа Идентификатор="...">
object_types = re.findall(r'<(msg:\w+)\s', body_content)
print("\n=== ТИПЫ ОБЪЕКТОВ В BODY ===")
for t, c in Counter(object_types).most_common():
    print(f"  {t}: {c}")

# Ищем EnterpriseData блоки
ed_blocks = re.findall(r'<EnterpriseData[^>]*>(.*?)</EnterpriseData>', body_content, re.DOTALL)
print(f"\n=== КОЛИЧЕСТВО EnterpriseData блоков: {len(ed_blocks)} ===")

# Анализируем структуру каждого EnterpriseData блока
for i, block in enumerate(ed_blocks[:5]):  # Первые 5 блоков
    print(f"\n--- EnterpriseData блок {i+1} ---")
    # Ищем все теги верхнего уровня внутри
    top_tags = re.findall(r'<(\w+)[>\s]', block)
    print(f"  Теги: {Counter(top_tags).most_common(10)}")
    # Показываем первые 500 символов
    print(f"  Фрагмент: {block[:500]}...")

# Ищем все документы и справочники
print("\n\n=== ПОИСК ВСЕХ ТИПОВ ДОКУМЕНТОВ И СПРАВОЧНИКОВ ===")

# Ищем все вхождения <ИмяОбъектаМетаданных> или подобные
# В EnterpriseData формате типы объектов выглядят как:
# <Catalog_Номенклатура>, <Document_РеализацияТоваровУслуг> и т.д.

# Ищем все теги, которые могут быть типами объектов
all_tags = re.findall(r'<(\w+)[>\s]', body_content)
tag_counter = Counter(all_tags)

# Фильтруем только теги, похожие на объекты метаданных
metadata_tags = [t for t in tag_counter.keys() if any(prefix in t for prefix in ['Catalog_', 'Document_', 'AccumulationRegister_', 'InformationRegister_', 'Enum_', 'ChartOfCharacteristicTypes_', 'BusinessProcess_', 'Task_'])]
print("Теги объектов метаданных:")
for t in sorted(metadata_tags):
    print(f"  {t}: {tag_counter[t]}")

# Также ищем в атрибутах
print("\n\n=== ПОИСК В АТРИБУТАХ ===")
attr_types = re.findall(r'ИмяОбъектаМетаданных="([^"]+)"', body_content)
print(f"ИмяОбъектаМетаданных: {Counter(attr_types).most_common()}")

# Ищем GUID объектов
guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', body_content)
print(f"\nВсего GUID: {len(guids)}")

# Ищем даты
dates = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', body_content)
print(f"Всего дат: {len(dates)}")
if dates:
    print(f"  Первые 5 дат: {dates[:5]}")
    print(f"  Последние 5 дат: {dates[-5:]}")

# Ищем суммы/числа
amounts = re.findall(r'>(\d+\.\d{2})<', body_content)
print(f"\nВсего сумм (с 2 знаками): {len(amounts)}")
if amounts:
    print(f"  Первые 10 сумм: {amounts[:10]}")

# Ищем названия
names = re.findall(r'<Наименование>([^<]+)</Наименование>', body_content)
print(f"\nВсего наименований: {len(names)}")
if names:
    print(f"  Первые 10 наименований: {names[:10]}")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
