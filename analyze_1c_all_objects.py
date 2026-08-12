#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Потоковый анализ всех объектов в XML-выгрузке 1С
"""

import os
import re
from collections import Counter

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)
print(f"Размер файла: {filesize:,} байт ({filesize/1024/1024:.2f} MB)")

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
    body_size = body_end_pos - body_start_pos
    print(f"Body: {body_start_pos} - {body_end_pos} ({body_size/1024/1024:.2f} MB)")

# Теперь читаем Body блоками и ищем все объекты
print("\n=== ПОИСК ВСЕХ ТИПОВ ОБЪЕКТОВ ===")

# Счетчики для каждого типа объекта
object_counters = {}
# Для хранения структуры (первые найденные поля)
object_structures = {}

with open(filepath, 'r', encoding='utf-8') as f:
    f.seek(body_start_pos)
    
    # Читаем блоками по 10MB
    block_size = 10 * 1024 * 1024
    bytes_read = 0
    buffer = ""
    
    while bytes_read < body_size:
        # Читаем следующий блок
        to_read = min(block_size, body_size - bytes_read)
        chunk = f.read(to_read)
        if not chunk:
            break
        
        bytes_read += len(chunk)
        buffer += chunk
        
        # Ищем все теги с точкой (объекты метаданных)
        obj_tags = re.findall(r'<(\w+\.\w+)', buffer)
        for tag in obj_tags:
            if tag not in object_counters:
                object_counters[tag] = 0
            object_counters[tag] += 1
        
        # Очищаем буфер, оставляя последние 10000 символов для контекста
        if len(buffer) > 100000:
            buffer = buffer[-10000:]
        
        if bytes_read % (20 * 1024 * 1024) == 0:
            print(f"  Прочитано {bytes_read/1024/1024:.0f} MB из {body_size/1024/1024:.0f} MB...")

print(f"\nВсего типов объектов: {len(object_counters)}")
for tag, count in sorted(object_counters.items(), key=lambda x: -x[1]):
    print(f"  {tag}: {count}")

# Теперь для каждого типа найдем структуру (поля)
print("\n\n=== СТРУКТУРА КАЖДОГО ТИПА ОБЪЕКТОВ ===")

with open(filepath, 'r', encoding='utf-8') as f:
    f.seek(body_start_pos)
    
    # Читаем первые 5MB для поиска структуры
    sample = f.read(5 * 1024 * 1024)
    
    for obj_type in sorted(object_counters.keys(), key=lambda x: -object_counters[x]):
        pattern = f'<{obj_type}[^>]*>(.*?)</{obj_type}>'
        match = re.search(pattern, sample, re.DOTALL)
        if match:
            block = match.group(1)
            inner_tags = set(re.findall(r'<(\w+)>', block))
            print(f"\n--- {obj_type} (всего: {object_counters[obj_type]}) ---")
            print(f"  Поля: {', '.join(sorted(inner_tags))}")
            # Покажем первые 150 символов
            print(f"  Пример: {block[:150]}...")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
