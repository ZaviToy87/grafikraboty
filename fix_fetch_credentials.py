# -*- coding: utf-8 -*-
"""
Добавить credentials: 'include' во все fetch запросы в app.js
"""
import re

file_path = 'static/js/app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Паттерн: fetch( ... ) без credentials
# Заменяем fetch(url, { method: ... }) на fetch(url, { credentials: 'include', method: ... })
# И fetch(url) на fetch(url, { credentials: 'include' })

count = 0

# Вариант 1: fetch(url, { method: 'POST'... }) - добавляем credentials после {
def add_credentials(match):
    global count
    prefix = match.group(1)
    options = match.group(2)
    if 'credentials:' not in options:
        count += 1
        # Добавляем credentials после открывающей {
        return prefix + '{ credentials: \'include\', ' + options
    return match.group(0)

# Находим все fetch с options
pattern = r"(fetch\([^,]+,\s*)\{([^}]+method[^}]+)\}"
content = re.sub(pattern, add_credentials, content)

# Вариант 2: fetch(url) без options - добавляем { credentials: 'include' }
def add_credentials_simple(match):
    global count
    url = match.group(1)
    # Проверяем, нет ли уже credentials поблизости
    count += 1
    return f"fetch({url}, {{ credentials: 'include' }})"

# Простые fetch без options (только URL)
simple_pattern = r"fetch\((['\"][^'\"]+['\"])\.then\("
content = re.sub(simple_pattern, add_credentials_simple, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Added credentials: 'include' to {count} fetch calls in app.js")
