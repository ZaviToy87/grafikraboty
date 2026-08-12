# -*- coding: utf-8 -*-
"""
Найти все проблемные строки с fetch в app.js
"""

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Строки с fetch и credentials ===\n")

for i, line in enumerate(lines, 1):
    if 'fetch' in line.lower() and 'api' in line.lower():
        # Показываем строку и следующую для контекста
        next_line = lines[i].rstrip() if i < len(lines) else ""
        print(f"Line {i}: {line.rstrip()[:100]}")
        if 'credentials' not in line and '{' not in line:
            print(f"         ^^^ NEEDS FIX - no credentials")
        if 'method:' in line and '})' not in line and ');' not in line:
            print(f"         ^^^ MAYBE BROKEN - missing closing")
        print()
