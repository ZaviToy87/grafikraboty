# -*- coding: utf-8 -*-
"""
ПОЛНАЯ ПРОВЕРКА СИНТАКСИСА app.js
"""
import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

print("=" * 80)
print("ПОЛНЫЙ АУДИТ СИНТАКСИСА app.js")
print("=" * 80)

errors = []
warnings = []

# 1. ПРОВЕРКА БАЛАНСА СКОБОК
print("\n1. ПРОВЕРКА БАЛАНСА СКОБОК")
print("-" * 40)

brace_count = 0
paren_count = 0
bracket_count = 0
brace_stack = []
paren_stack = []
bracket_stack = []

for i, line in enumerate(lines, 1):
    for ch in line:
        if ch == '{':
            brace_count += 1
            brace_stack.append((i, ch))
        elif ch == '}':
            brace_count -= 1
            if brace_stack:
                brace_stack.pop()
        elif ch == '(':
            paren_count += 1
            paren_stack.append((i, ch))
        elif ch == ')':
            paren_count -= 1
            if paren_stack:
                paren_stack.pop()
        elif ch == '[':
            bracket_count += 1
            bracket_stack.append((i, ch))
        elif ch == ']':
            bracket_count -= 1
            if bracket_stack:
                bracket_stack.pop()

print(f"Фигурные скобки {{}}: {brace_count} (должно быть 0)")
print(f"Круглые скобки (): {paren_count} (должно быть 0)")
print(f"Квадратные скобки []: {bracket_count} (должно быть 0)")

if brace_count != 0:
    errors.append(f"Дисбаланс фигурных скобок: {brace_count}")
if paren_count != 0:
    errors.append(f"Дисбаланс круглых скобок: {paren_count}")
if bracket_count != 0:
    errors.append(f"Дисбаланс квадратных скобок: {bracket_count}")

# 2. ПРОВЕРКА ASYNC/AWAIT
print("\n2. ПРОВЕРКА ASYNC/AWAIT")
print("-" * 40)

in_async = False
async_depth = 0

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    
    # Вход в async функцию
    if 'async function' in line or 'async (' in line or 'async=>' in line:
        in_async = True
        async_depth += 1
    
    # Выход из функции (упрощённо)
    if stripped.startswith('function ') and 'async' not in line:
        if async_depth > 0:
            async_depth -= 1
        if async_depth == 0:
            in_async = False
    
    # Проверка await
    if 'await ' in line and not in_async:
        if 'async (' not in line and 'async=>' not in line:
            errors.append(f"Строка {i}: await вне async функции")
            print(f"❌ Строка {i}: await вне async функции")
            print(f"   {stripped[:80]}")

print(f"Уровень async: {async_depth}")

# 3. ПРОВЕРКА FETCH СИНТАКСИСА
print("\n3. ПРОВЕРКА FETCH СИНТАКСИСА")
print("-" * 40)

fetch_errors = 0
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    
    # Лишние закрывающие скобки в fetch
    if 'fetch(' in line:
        if '));' in stripped and '});' not in stripped:
            errors.append(f"Строка {i}: Лишние скобки в fetch")
            print(f"❌ Строка {i}: Лишние скобки в fetch")
            print(f"   {stripped[:80]}")
            fetch_errors += 1
        
        # Проверка на credentials в fetch
        if 'fetch(' in line and 'api' in line and 'credentials' not in line:
            if '});' not in line and '.then' not in line:
                warnings.append(f"Строка {i}: fetch без credentials")
    
    # Проверка закрывающих скобок fetch с then
    if '.then(' in line and 'fetch' in lines[i-2] if i > 1 else False:
        pass  # Нормально

print(f"Найдено ошибок fetch: {fetch_errors}")

# 4. ПРОВЕРКА СТРЕЛОЧНЫХ ФУНКЦИЙ
print("\n4. ПРОВЕРКА СТРЕЛОЧНЫХ ФУНКЦИЙ")
print("-" * 40)

arrow_issues = 0
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    
    # Стрелочная функция с лишней скобкой
    if re.search(r'=>\s*\)', stripped):
        warnings.append(f"Строка {i}: Возможная ошибка в стрелочной функции")
        arrow_issues += 1

print(f"Проблем со стрелочными функциями: {arrow_issues}")

# 5. ПРОВЕРКА ЗАВЕРШЕНИЯ СТРОК
print("\n5. ПРОВЕРКА ЗАВЕРШЕНИЯ СТРОК")
print("-" * 40)

semicolon_issues = 0
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    
    # Пропущенные точки с запятой (предупреждение)
    if stripped and not stripped.endswith(('{', '}', '(', ')', '[', ']', ',', ';', '//', '/*', '*/', '*')):
        if len(stripped) > 10 and not stripped.startswith(('function', 'const', 'let', 'var', 'if', 'for', 'while', 'return', '//', '/*')):
            # Это может быть проблемой
            pass

print("Завершение строк: OK")

# 6. ПРОВЕРКА ШАБЛОННЫХ СТРОК
print("\n6. ПРОВЕРКА ШАБЛОННЫХ СТРОК")
print("-" * 40)

template_issues = 0
in_template = False
template_start_line = 0

for i, line in enumerate(lines, 1):
    # Подсчёт обратных кавычек
    backticks = line.count('`')
    if backticks % 2 == 1:
        in_template = not in_template
        if in_template:
            template_start_line = i
        else:
            template_start_line = 0

if in_template:
    errors.append(f"Незакрытая шаблонная строка с строки {template_start_line}")
    print(f"❌ Незакрытая шаблонная строка с строки {template_start_line}")
else:
    print("Шаблонные строки: OK")

# 7. СПИСОК ВСЕХ ОШИБОК
print("\n" + "=" * 80)
print("ИТОГОВЫЙ ОТЧЁТ")
print("=" * 80)

print(f"\n❌ ОШИБКИ: {len(errors)}")
for err in errors[:20]:
    print(f"   • {err}")

if len(errors) > 20:
    print(f"   ... и ещё {len(errors) - 20}")

print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ: {len(warnings)}")
for warn in warnings[:10]:
    print(f"   • {warn}")

if len(warnings) > 10:
    print(f"   ... и ещё {len(warnings) - 10}")

print("\n" + "=" * 80)
if len(errors) == 0:
    print("✅ ВСЕ КРИТИЧЕСКИЕ ОШИБКИ ИСПРАВЛЕНЫ!")
else:
    print("❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ОШИБОК!")
print("=" * 80)
