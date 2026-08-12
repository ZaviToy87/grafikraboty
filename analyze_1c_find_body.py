#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск Body в XML
"""

import os
import re

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'

print("Читаем файл...")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем все вхождения "Body" в разных регистрах
for match in re.finditer(r'.{0,20}Body.{0,20}', content, re.IGNORECASE):
    pos = match.start()
    print(f"Позиция {pos}: ...{match.group()}...")

# Также ищем просто <Body
print("\n\n=== Поиск <Body ===")
for match in re.finditer(r'<Body[^>]*>', content):
    pos = match.start()
    print(f"Позиция {pos}: {match.group()}")

# Ищем </Body>
print("\n\n=== Поиск </Body> ===")
for match in re.finditer(r'</Body>', content):
    pos = match.start()
    print(f"Позиция {pos}: {match.group()}")

# Ищем msg:Body
print("\n\n=== Поиск msg:Body ===")
for match in re.finditer(r'msg:Body', content):
    pos = match.start()
    print(f"Позиция {pos}: {match.group()}")

# Покажем что вокруг позиции 3000 (где заканчивается Header)
print("\n\n=== Контент вокруг позиции 3000 ===")
print(content[2500:3500])

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
