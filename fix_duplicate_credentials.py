# -*- coding: utf-8 -*-
"""
Удалить дубликаты credentials в app.js
"""

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Удаляем дубликаты credentials
import re

# Паттерн: credentials: 'include', ... credentials: 'include'
content = re.sub(
    r"credentials: 'include',\s*([^}]*?)credentials: 'include',",
    r"credentials: 'include', \1",
    content
)

# Также паттерн где credentials в конце повторяется
content = re.sub(
    r"credentials: 'include'\s*credentials: 'include'",
    r"credentials: 'include'",
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Removed duplicate credentials")

# Проверяем баланс
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print(f"Balanced: {open_braces == close_braces}")
