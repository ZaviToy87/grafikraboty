# -*- coding: utf-8 -*-
"""
Восстановить app.js - добавить credentials правильно
"""
import re

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Считаем оригинальные скобки
orig_open = content.count('{')
orig_close = content.count('}')
print(f"Before: {orig_open} open, {orig_close} close, balanced={orig_open == orig_close}")

# 1. Исправляем fetch('/api/...').then() → fetch('/api/...', {credentials}).then()
def fix_simple_fetch(match):
    url = match.group(1)
    then_part = match.group(2)
    return f"fetch({url}, {{ credentials: 'include' }}).then({then_part}"

content = re.sub(
    r"fetch\((['\"][^'\"]+['\"])\)\.then\((.+?)\)",
    fix_simple_fetch,
    content,
    flags=re.DOTALL
)

# 2. Исправляем await fetch('/api/...', { method: ... }) → await fetch('/api/...', { credentials, method })
def fix_await_fetch(match):
    full = match.group(0)
    if 'credentials' in full:
        return full  # Уже есть credentials
    
    # Находим options объект
    start = full.find('{')
    end = full.rfind('}')
    if start == -1 or end == -1:
        return full
    
    options = full[start:end+1]
    # Добавляем credentials в начало options
    new_options = '{ credentials: \'include\', ' + options[1:]
    return full[:start] + new_options + full[end+1:]

# await fetch с options
content = re.sub(
    r"await fetch\([^)]+\{[^}]+\}",
    fix_await_fetch,
    content
)

# 3. Исправляем синтаксические ошибки
content = content.replace("method: 'DELETE' )", "method: 'DELETE' })")
content = content.replace("method: 'POST' )", "method: 'POST' })")
content = content.replace("method: 'PUT' )", "method: 'PUT' })")
content = content.replace("method: 'PATCH' )", "method: 'PATCH' })")

# 4. Удаляем дубликаты credentials
content = re.sub(
    r"credentials: 'include',\s*credentials: 'include',",
    "credentials: 'include',",
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Проверяем результат
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_open = content.count('{')
new_close = content.count('}')
print(f"After: {new_open} open, {new_close} close, balanced={new_open == new_close}")

if new_open == new_close:
    print("✅ app.js исправлен и сбалансирован!")
else:
    print(f"⚠️ Всё ещё есть дисбаланс: {abs(new_open - new_close)} скобок")
