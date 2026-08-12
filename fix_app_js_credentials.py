# -*- coding: utf-8 -*-
"""
Исправить fetch запросы в app.js - добавить credentials: 'include'
Без поломки синтаксиса
"""

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_count = 0
new_lines = []

for i, line in enumerate(lines):
    # Ищем fetch('/api/...') без credentials
    if "fetch('/api/" in line and 'credentials' not in line and '.then(' in line:
        # Это простая конструкция fetch(url).then() - заменяем на fetch(url, {credentials}).then()
        if ".then(" in line:
            # Находим позицию перед .then(
            parts = line.split('.then(')
            if len(parts) == 2:
                url_part = parts[0].rstrip()
                then_part = parts[1]
                # Проверяем, есть ли уже options
                if url_part.endswith(')'):
                    # Удаляем последнюю ) и добавляем credentials
                    url_part = url_part[:-1] + ", { credentials: 'include' })"
                new_line = url_part + '.then(' + then_part
                new_lines.append(new_line)
                fixed_count += 1
                continue
    
    # Ищем await fetch('/api/...') без credentials  
    if "await fetch('/api/" in line and 'credentials' not in line:
        # Проверяем, есть ли уже options в этой строке
        if '{' not in line or 'method' in line:
            # Находим позицию перед )
            if ', {' in line:
                # Уже есть options, добавляем credentials
                new_line = line.replace(', {', ", { credentials: 'include', ", 1)
                new_lines.append(new_line)
                fixed_count += 1
                continue
            elif line.strip().endswith(') {'):
                # Простой fetch без options
                new_line = line.replace(') {', ", { credentials: 'include' }) {", 1)
                new_lines.append(new_line)
                fixed_count += 1
                continue
    
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ Fixed {fixed_count} fetch calls")

# Проверяем баланс скобок
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print(f"Balanced: {open_braces == close_braces}")
