import re

with open('main_launcher.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим строку с "def _notify_telegram_and_hint"
for i, line in enumerate(lines):
    if 'def _notify_telegram_and_hint' in line:
        print(f"Found at line {i+1}: {line.strip()}")
        # Показываем контекст
        for j in range(max(0, i-2), min(len(lines), i+10)):
            marker = ">>> " if j == i else "    "
            print(f"{marker}{j+1}: {lines[j].rstrip()}")
        break
