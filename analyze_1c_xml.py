#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры XML-выгрузки из 1С (формат EnterpriseData)
"""

import xml.etree.ElementTree as ET
import os
import re
from collections import Counter

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)
print(f"Размер файла: {filesize:,} байт ({filesize/1024/1024:.2f} MB)")

# Читаем первые 50000 символов для анализа структуры
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read(50000)

# Найдем все открывающие теги (без атрибутов)
tags = re.findall(r'<(\w+)[>\s]', content)
tag_counter = Counter(tags)

print("\n=== ТЕГИ (первые 50 по частоте) ===")
for tag, count in tag_counter.most_common(50):
    print(f"  {tag}: {count}")

# Найдем структуру вложенности
print("\n=== СТРУКТУРА XML (первые 200 строк) ===")
lines = content.split('\n')
for i, line in enumerate(lines[:200]):
    print(f"{i+1:4d} | {line}")

# Определим корневой элемент
print("\n=== КОРНЕВОЙ ЭЛЕМЕНТ ===")
# Ищем первый тег после <?xml
match = re.search(r'<(\w+)\s', content[content.find('?>'):])
if match:
    print(f"Корневой тег: {match.group(1)}")

# Ищем пространства имен
ns_matches = re.findall(r'xmlns:(\w+)="([^"]+)"', content[:2000])
print("\n=== ПРОСТРАНСТВА ИМЕН ===")
for prefix, uri in ns_matches:
    print(f"  {prefix}: {uri}")

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
