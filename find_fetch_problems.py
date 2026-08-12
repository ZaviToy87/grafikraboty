# -*- coding: utf-8 -*-
"""
Найти все строки с fetch в app.js и проверить синтаксис
"""

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Проблемные строки fetch ===\n")

for i, line in enumerate(lines, 1):
    if 'fetch' in line and ('api' in line or 'chat' in line or 'schedule' in line):
        # Проверяем на явные проблемы
        problems = []
        
        # Дубликат credentials
        if line.count('credentials') > 1:
            problems.append('DUPLICATE credentials')
        
        # Нет закрывающей скобки
        if 'credentials' in line and '});' not in line and '.then' not in line:
            # Проверяем следующую строку
            if i < len(lines):
                next_line = lines[i]
                if '});' not in next_line and '.then' not in next_line:
                    problems.append('Missing closing });')
        
        # Неправильный синтаксис method
        if "method: 'DELETE' )" in line or "method: 'POST' )" in line:
            problems.append('Bad method syntax')
        
        if problems:
            print(f"Line {i}: {', '.join(problems)}")
            print(f"  {line.rstrip()[:120]}")
            if i < len(lines):
                print(f"  {lines[i].rstrip()[:120]}")
            print()
