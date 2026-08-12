# -*- coding: utf-8 -*-
"""
Исправить все проблемы с fetch в app.js
"""

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем: headers: { 'Content-Type': 'application/json' , → headers: { 'Content-Type': 'application/json' },
content = content.replace(
    "headers: { 'Content-Type': 'application/json' ,",
    "headers: { 'Content-Type': 'application/json' },"
)

# Исправляем: headers: { 'Content-Type': 'application/json'  → headers: { 'Content-Type': 'application/json' },
content = content.replace(
    "headers: { 'Content-Type': 'application/json' ",
    "headers: { 'Content-Type': 'application/json' }, "
)

# Исправляем method: 'DELETE' ) → method: 'DELETE' })
content = content.replace("method: 'DELETE' )", "method: 'DELETE' })")
content = content.replace("method: 'POST' )", "method: 'POST' })")
content = content.replace("method: 'PUT' )", "method: 'PUT' })")
content = content.replace("method: 'PATCH' )", "method: 'PATCH' })")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed fetch syntax")

# Проверяем баланс
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print(f"Balanced: {open_braces == close_braces}")
