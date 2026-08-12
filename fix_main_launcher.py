# -*- coding: utf-8 -*-
"""
Исправление main_launcher.py — правильная вставка VK уведомления
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
main_launcher_path = os.path.join(BASE_DIR, 'main_launcher.py')

print(f"Fixing: {main_launcher_path}")

with open(main_launcher_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим проблемные строки и исправляем
new_lines = []
skip_next_docstring = False

for i, line in enumerate(lines):
    # Исправляем строку 1470 — добавляем двоеточие
    if i == 1469 and 'def _notify_telegram_and_hint(local_ip, link_local, link_public)' in line and not line.strip().endswith(':'):
        new_lines.append(line.rstrip() + ':\n')
        print(f"Fixed line {i+1}: added colon")
    
    # Пропускаем строку 1473 (неправильный вызов функции с двоеточием)
    elif i == 1472 and '_send_vk_startup_notification(local_ip, link_local, link_public):' in line:
        new_lines.append('    _send_vk_startup_notification(local_ip, link_local, link_public)\n')
        print(f"Fixed line {i+1}: removed colon from function call")
    
    # Пропускаем строку с docstring если она идёт после нашего вызова
    elif skip_next_docstring and '"""' in line and 'Запустит туннель' in line:
        print(f"Skipped docstring line {i+1}")
        skip_next_docstring = False
    
    # Пропускаем дублирующий docstring
    elif i == 1474 and '"""Р—Р°РїСѓсС‚иС‚СЊ С‚СѓРЅнеР»СЊ' in line:
        print(f"Skipped duplicate docstring line {i+1}")
        continue
    
    else:
        new_lines.append(line)

with open(main_launcher_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Fixed!")
