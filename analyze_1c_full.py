#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный анализ XML-выгрузки из 1С с seek
"""

import os
import re
from collections import Counter

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)
print(f"Размер файла: {filesize:,} байт ({filesize/1024/1024:.2f} MB)")

with open(filepath, 'r', encoding='utf-8') as f:
    # Ищем <Body в начале
    chunk = f.read(50000)
    body_tag_start = chunk.find('<Body')
    body_tag_end = chunk.find('>', body_tag_start) + 1
    
    print(f"<Body на позиции: {body_tag_start}")
    print(f"Тег Body: {chunk[body_tag_start:body_tag_end]}")
    
    # Ищем </Body> с конца файла
    # Читаем последние 1000 байт
    f.seek(filesize - 2000)
    tail = f.read(2000)
    body_close = tail.rfind('</Body>')
    
    if body_close >= 0:
        # Вычисляем абсолютную позицию
        body_close_abs = filesize - 2000 + body_close
        print(f"</Body> на позиции: {body_close_abs}")
        
        # Читаем содержимое Body
        body_start_pos = body_tag_end
        body_end_pos = body_close_abs
        body_size = body_end_pos - body_start_pos
        print(f"Размер Body: {body_size} байт ({body_size/1024/1024:.2f} MB)")
        
        # Читаем первые 500KB для анализа
        f.seek(body_start_pos)
        body_sample = f.read(min(body_size, 500000))
        
        print("\n=== ПЕРВЫЕ 2000 СИМВОЛОВ BODY ===")
        print(body_sample[:2000])
        
        print("\n\n=== ОБЪЕКТЫ МЕТАДАННЫХ ===")
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
        
        # Теперь прочитаем последние 500KB для анализа
        print("\n\n=== ПОСЛЕДНИЕ 2000 СИМВОЛОВ BODY ===")
        f.seek(body_end_pos - 2000)
        body_tail = f.read(2000)
        print(body_tail)

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
