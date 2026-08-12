#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры документов и штрихкодов в выгрузке 1С
"""

import os
import re
from collections import Counter

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)

# Найдем границы Body
with open(filepath, 'r', encoding='utf-8') as f:
    chunk = f.read(50000)
    body_tag_start = chunk.find('<Body')
    body_tag_end = chunk.find('>', body_tag_start) + 1
    f.seek(filesize - 2000)
    tail = f.read(2000)
    body_close = tail.rfind('</Body>')
    body_close_abs = filesize - 2000 + body_close
    body_start_pos = body_tag_end
    body_end_pos = body_close_abs

# Читаем Body целиком (он 143 MB, но мы можем читать частями)
# Сначала найдем все документы
print("=== АНАЛИЗ ДОКУМЕНТОВ ===")

doc_types = [
    'Документ.ОтчетОРозничныхПродажах',
    'Документ.ОприходованиеТоваров',
    'Документ.ПКОРозничнаяВыручка',
    'Документ.ВыемкаДСИзКассыККМ',
    'Документ.ПКОРасчетыСКонтрагентами',
    'Документ.РКОПрочаяВыдача',
    'Документ.ВнесениеДСВКассуККМ',
    'Документ.ИнвентаризацияТоваров',
    'Справочник.ШтрихкодыНоменклатуры',
    'Справочник.Контрагенты',
    'Справочник.Договоры',
    'Справочник.Организации',
    'Справочник.Склады',
    'Справочник.КассыККМ',
    'Справочник.ДисконтныеКарты',
    'Справочник.ФизическиеЛица',
    'Справочник.Пользователи',
    'Справочник.МаркировкаУпаковки',
]

with open(filepath, 'r', encoding='utf-8') as f:
    f.seek(body_start_pos)
    # Читаем первые 20MB для поиска структуры всех типов
    sample = f.read(20 * 1024 * 1024)
    
    for obj_type in doc_types:
        pattern = f'<{obj_type}[^>]*>(.*?)</{obj_type}>'
        match = re.search(pattern, sample, re.DOTALL)
        if match:
            block = match.group(1)
            inner_tags = set(re.findall(r'<(\w+)>', block))
            print(f"\n--- {obj_type} ---")
            print(f"  Поля: {', '.join(sorted(inner_tags))}")
            print(f"  Пример: {block[:300]}...")
        else:
            print(f"\n--- {obj_type} ---")
            print(f"  (не найден в первых 20MB)")

# Теперь найдем примеры продаж (ОтчетОРозничныхПродажах) - это самое важное
print("\n\n=== ПРИМЕРЫ ДОКУМЕНТОВ ===")

with open(filepath, 'r', encoding='utf-8') as f:
    f.seek(body_start_pos)
    # Ищем ОтчетОРозничныхПродажах
    content = f.read(100 * 1024 * 1024)  # 100MB
    
    # Найдем первый документ продажи
    for doc_name in ['Документ.ОтчетОРозничныхПродажах', 'Документ.ОприходованиеТоваров', 'Документ.ПКОРозничнаяВыручка']:
        pattern = f'<{doc_name}[^>]*>(.*?)</{doc_name}>'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            block = match.group(1)
            print(f"\n=== {doc_name} (ПОЛНЫЙ ПРИМЕР) ===")
            print(block[:1000])

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
