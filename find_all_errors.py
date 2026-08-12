# -*- coding: utf-8 -*-
"""
Найти ВСЕ синтаксические ошибки в app.js
"""

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

errors = []

for i, line in enumerate(lines, 1):
    s = line.rstrip()
    
    # 1. Лишние закрывающие скобки в fetch
    if '));' in s and ('fetch' in s or 'await' in s):
        errors.append((i, 'EXTRA PAREN', s[:80]))
    
    # 2. Двойные закрывающие скобки
    if '}).catch' not in s and '}).then' not in s:
        if '}, },' in s or '},}' in s or '}, }' in s:
            errors.append((i, 'DOUBLE BRACE', s[:80]))
    
    # 3. Неправильные headers
    if "headers: {" in s and s.count('{') != s.count('}'):
        errors.append((i, 'HEADERS BRACE', s[:80]))
    
    # 4. method с лишней скобкой
    if "method: 'DELETE' )" in s or "method: 'POST' )" in s:
        errors.append((i, 'METHOD BRACE', s[:80]))
    
    # 5. fetch без закрывающей
    if 'fetch(' in s and '});' not in s and '.then' not in s and '{' not in s:
        if s.count('(') > s.count(')'):
            errors.append((i, 'MISSING CLOSE', s[:80]))

print(f'=== НАЙДЕНО {len(errors)} ОШИБОК ===\n')

for num, err_type, err_line in errors[:50]:
    print(f'{num} [{err_type}]: {err_line}')

if len(errors) > 50:
    print(f'... и ещё {len(errors) - 50}')
