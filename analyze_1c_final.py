#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальный анализ XML-выгрузки из 1С
"""

import os
import re
from collections import Counter

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)
print(f"Размер файла: {filesize:,} байт ({filesize/1024/1024:.2f} MB)")

# Используем seek для чтения Body
with open(filepath, 'r', encoding='utf-8') as f:
    # Ищем <Body (с атрибутами)
    chunk = f.read(50000)
    body_tag_start = chunk.find('<Body')
    body_tag_end = chunk.find('>', body_tag_start) + 1
    body_close = chunk.find('</Body>')
    
    print(f"<Body найден на позиции: {body_tag_start}")
    print(f"Тег Body: {chunk[body_tag_start:body_tag_end]}")
    print(f"</Body> на позиции: {body_close}")
    
    if body_tag_start >= 0 and body_close >= 0:
        # Читаем содержимое Body
        body_start_pos = body_tag_end
        body_end_pos = body_close
        
        # Переходим на позицию после <Body ...>
        f.seek(body_start_pos)
        
        # Читаем содержимое Body
        body_size = body_end_pos - body_start_pos
        print(f"Размер Body: {body_size} байт")
        
        # Читаем первые 500KB для анализа
        body_sample = f.read(min(body_size, 500000))
        
        print("\n=== ПЕРВЫЕ 2000 СИМВОЛОВ BODY ===")
        print(body_sample[:2000])
        
        print("\n\n=== ОБЪЕКТЫ МЕТАДАННЫХ ===")
        # Ищем теги вида Справочник.XXX, Документ.XXX и т.д.
        obj_tags = re.findall(r'<(\w+\.\w+)', body_sample)
        obj_counter = Counter(obj_tags)
        
        print(f"Всего типов объектов (в первых 500KB): {len(obj_counter)}")
        for tag, count in obj_counter.most_common():
            print(f"  {tag}: {count}")
        
        # Для каждого типа покажем структуру
        print("\n\n=== СТРУКТУРА ОБЪЕКТОВ ===")
        for obj_type, count in obj_counter.most_common():
            pattern = f'<{obj_type}[^>]*>(.*?)</{obj_type}>'
            match = re.search(pattern, body_sample, re.DOTALL)
            if match:
                block = match.group(1)
                inner_tags = set(re.findall(r'<(\w+)>', block))
                print(f"\n--- {obj_type} (всего: {count}) ---")
                print(f"  Поля: {', '.join(sorted(inner_tags))}")
                print(f"  Пример: {block[:200]}...")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
