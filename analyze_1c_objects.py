#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ объектов метаданных в выгрузке 1С
"""

import os
import re
from collections import Counter, defaultdict

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'

print("Читаем файл...")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим Body (без префикса msg:)
body_start = content.find('<Body>')
body_end = content.find('</Body>')
body_content = content[body_start:body_end]

print(f"Body размер: {len(body_content)} символов")

# Ищем все справочники и документы верхнего уровня
# Формат: <Справочник.Имя> или <Документ.Имя> или <РегистрНакопления.Имя>
print("\n=== ОБЪЕКТЫ МЕТАДАННЫХ В BODY ===")

# Ищем все теги, содержащие точку (это объекты метаданных)
all_tags = re.findall(r'<(\w+\.\w+)', body_content)
tag_counter = Counter(all_tags)

print(f"\nВсего типов объектов: {len(tag_counter)}")
for tag, count in tag_counter.most_common():
    print(f"  {tag}: {count}")

# Теперь давайте посмотрим на структуру каждого типа объектов
print("\n\n=== СТРУКТУРА КАЖДОГО ТИПА ОБЪЕКТОВ ===")

# Для каждого типа найдем первый блок и покажем его структуру
for obj_type, count in tag_counter.most_common():
    # Найдем первый блок этого типа
    pattern = f'<{obj_type}[^>]*>(.*?)</{obj_type}>'
    match = re.search(pattern, body_content, re.DOTALL)
    if match:
        block = match.group(1)
        # Найдем все теги внутри блока
        inner_tags = set(re.findall(r'<(\w+)>', block))
        print(f"\n--- {obj_type} (всего: {count}) ---")
        print(f"  Поля: {', '.join(sorted(inner_tags))}")
        # Покажем первые 300 символов примера
        print(f"  Пример: {block[:300]}...")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
