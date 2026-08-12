# -*- coding: utf-8 -*-
"""
Полная отладка VK вложений
Показывает ВСЮ структуру события VK
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'vk_bot.log')

print("=" * 80)
print(" ОТЛАДКА VK ВЛОЖЕНИЙ")
print("=" * 80)
print()

if not os.path.exists(LOG_FILE):
    print(f"❌ Лог не найден: {LOG_FILE}")
    print("Отправь фото в VK чат и перезапусти сервер")
    sys.exit(1)

print(f"📄 Читаем лог: {LOG_FILE}")
print()

# Читаем последние 100 строк с "attachments"
try:
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    found = False
    attachment_lines = []
    
    for i, line in enumerate(lines[-200:], start=max(0, len(lines)-200)):
        if 'attachments' in line.lower() or 'MULTIPLE' in line or 'Attachment' in line:
            attachment_lines.append((i, line.strip()))
            found = True
    
    if not found:
        print("⚠️ В логах нет записей о вложениях")
        print()
        print("Отправь 3-5 фото в VK чат группы")
        print("Подожди 10 секунд")
        print("Запусти этот скрипт снова")
    else:
        print(f"✅ Найдено {len(attachment_lines)} записей о вложениях:")
        print()
        for line_num, line in attachment_lines[-20:]:  # Последние 20
            print(f"[{line_num}] {line}")
        
        print()
        print("=" * 80)
        print(" ПОЛНАЯ СТРУКТУРА VK СОБЫТИЯ")
        print("=" * 80)
        print()
        
        # Ищем полные структуры
        for i, line in enumerate(lines[-200:], start=max(0, len(lines)-200)):
            if 'event_data keys:' in line or 'message keys:' in line:
                print(f"[{i}] {line.strip()}")
        
        print()
        print("=" * 80)
        print(" РЕКОМЕНДАЦИИ")
        print("=" * 80)
        print()
        
        # Проверяем количество вложений
        multiple_found = False
        for line in lines[-200:]:
            if 'MULTIPLE ATTACHMENTS:' in line:
                multiple_found = True
                print(f"✅ Найдено множественные вложения: {line.strip()}")
        
        if not multiple_found:
            print("❌ Множественные вложения НЕ найдены в логах")
            print()
            print("Возможные причины:")
            print("1. VK Long Poll не передаёт все вложения")
            print("2. Вложения передаются в другом формате")
            print("3. Нужно использовать VK API для получения полного списка")
            print()
            print("Решение:")
            print("- Проверь https://vk.com/dev/bots_docs?f=5.+События")
            print("- VK может передавать вложения через callback API, а не Long Poll")
            
except Exception as e:
    print(f"❌ Ошибка чтения лога: {e}")

print()
