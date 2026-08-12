# -*- coding: utf-8 -*-
"""
ОТКАТ: Удалить все credentials из app.js и восстановить оригинальный синтаксис
"""

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# 1. Удаляем credentials: 'include', везде
content = content.replace("{ credentials: 'include', ", '{ ')
content = content.replace(", { credentials: 'include' }", ')')
content = content.replace("{ credentials: 'include' }", '')
content = content.replace("credentials: 'include',", '')
content = content.replace("credentials: 'include'", '')

# 2. Исправляем двойные запятые
content = content.replace(', ,', ',')
content = content.replace(',  ', ', ')
content = content.replace('{  ', '{ ')
content = content.replace('  }', ' }')

# 3. Исправляем headers с лишними скобками
content = content.replace("headers: { 'Content-Type': 'application/json' },", 
                          "headers: { 'Content-Type': 'application/json' },")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Removed all credentials")

# Проверяем баланс
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print(f"Balanced: {open_braces == close_braces}")
print(f"Diff: {open_braces - close_braces}")
