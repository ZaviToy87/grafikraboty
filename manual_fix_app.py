# -*- coding: utf-8 -*-
"""
Ручное исправление app.js - найти и исправить все синтаксические ошибки
"""

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = []
for i, line in enumerate(lines, 1):
    original = line
    
    # 1. Исправляем fetch с лишними скобками
    if "fetch('/" in line and '));' in line:
        line = line.replace('));', ');')
        fixed.append((i, 'removed extra )', original.rstrip(), line.rstrip()))
    
    # 2. Исправляем headers с лишней закрывающей скобкой
    if "headers: { 'Content-Type': 'application/json' }," in line:
        # Проверяем, нет ли лишней закрывающей
        if '}}' in line or line.strip().endswith('},'):
            line = line.replace("headers: { 'Content-Type': 'application/json' },", 
                               "headers: { 'Content-Type': 'application/json' },")
    
    # 3. Исправляем method с лишней скобкой
    if "method: 'DELETE' )" in line:
        line = line.replace("method: 'DELETE' )", "method: 'DELETE' })")
        fixed.append((i, 'fixed DELETE', original.rstrip(), line.rstrip()))
    
    if "method: 'POST' )" in line:
        line = line.replace("method: 'POST' )", "method: 'POST' })")
        fixed.append((i, 'fixed POST', original.rstrip(), line.rstrip()))
        
    if "method: 'PUT' )" in line:
        line = line.replace("method: 'PUT' )", "method: 'PUT' })")
        fixed.append((i, 'fixed PUT', original.rstrip(), line.rstrip()))
        
    if "method: 'PATCH' )" in line:
        line = line.replace("method: 'PATCH' )", "method: 'PATCH' })")
        fixed.append((i, 'fixed PATCH', original.rstrip(), line.rstrip()))
    
    lines[i-1] = line

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'Исправлено {len(fixed)} строк:')
for num, desc, orig, new in fixed[:20]:
    print(f'\n{num} [{desc}]:')
    print(f'  - {orig[:80]}')
    print(f'  + {new[:80]}')

# Проверяем баланс
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

open_b = content.count('{')
close_b = content.count('}')
print(f'\n=== БАЛАНС ===')
print(f'Открыто: {open_b}')
print(f'Закрыто: {close_b}')
print(f'Разница: {open_b - close_b}')
print(f'Сбалансировано: {open_b == close_b}')
