# -*- coding: utf-8 -*-
"""
Исправить синтаксические ошибки в app.js после добавления credentials
"""

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем ошибки:
# 1. method: 'DELETE' ) -> method: 'DELETE' })
content = content.replace("method: 'DELETE' );", "method: 'DELETE' });")
content = content.replace("method: 'DELETE' )", "method: 'DELETE' })")

# 2. method: 'POST' ) -> method: 'POST' })
content = content.replace("method: 'POST' );", "method: 'POST' });")
content = content.replace("method: 'POST' )", "method: 'POST' })")

# 3. method: 'PUT' ) -> method: 'PUT' })
content = content.replace("method: 'PUT' );", "method: 'PUT' });")
content = content.replace("method: 'PUT' )", "method: 'PUT' })")

# 4. method: 'PATCH' ) -> method: 'PATCH' })
content = content.replace("method: 'PATCH' );", "method: 'PATCH' });")
content = content.replace("method: 'PATCH' )", "method: 'PATCH' })")

# 5. Исправляем двойные credentials
content = content.replace("credentials: 'include', \n            credentials: 'include',", "credentials: 'include',")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed syntax errors")

# Проверяем баланс
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print(f"Balanced: {open_braces == close_braces}")
