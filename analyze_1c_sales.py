#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры продаж и штрихкодов
"""

import os
import re

filepath = r'C:\Users\User\Desktop\Выгрузка 1с\Message_РТ_РТ.xml'
filesize = os.path.getsize(filepath)

# Найдем границы Body
with open(filepath, 'r', encoding='utf-8') as f:
    chunk = f.read(50000)
    body_tag_start = chunk.find('<Body')
    body_tag_end = chunk.find('>', body_tag_start) + 1
    f.seek(filesize - 2000)
    tail = f.read(2000)
    body_close = tail.rfind('</Body>')
    body_close_abs = filesize - 2000 + body_close
    body_start_pos = body_tag_end

# Читаем 100MB для поиска
with open(filepath, 'r', encoding='utf-8') as f:
    f.seek(body_start_pos)
    content = f.read(100 * 1024 * 1024)

# Полная структура ОтчетОРозничныхПродажах
print("=== ПОЛНАЯ СТРУКТУРА ДОКУМЕНТА ПРОДАЖИ ===")
pattern = r'<Документ\.ОтчетОРозничныхПродажах[^>]*>(.*?)</Документ\.ОтчетОРозничныхПродажах>'
match = re.search(pattern, content, re.DOTALL)
if match:
    full_doc = match.group(1)
    print(full_doc[:2000])

# Структура ТоварыПродажа (табличная часть)
print("\n\n=== СТРУКТУРА ТОВАРЫ ПРОДАЖИ ===")
pattern = r'<ТоварыПродажа>(.*?)</ТоварыПродажа>'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:1000])

# Структура ШтрихкодыНоменклатуры
print("\n\n=== СТРУКТУРА ШТРИХКОДОВ ===")
pattern = r'<Справочник\.ШтрихкодыНоменклатуры[^>]*>(.*?)</Справочник\.ШтрихкодыНоменклатуры>'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:1000])

# Структура Контрагенты
print("\n\n=== СТРУКТУРА КОНТРАГЕНТОВ ===")
pattern = r'<Справочник\.Контрагенты[^>]*>(.*?)</Справочник\.Контрагенты>'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:1000])

# Структура Договоры
print("\n\n=== СТРУКТУРА ДОГОВОРОВ ===")
pattern = r'<Справочник\.Договоры[^>]*>(.*?)</Справочник\.Договоры>'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:1000])

# Структура ОприходованиеТоваров (приемка)
print("\n\n=== ПОЛНАЯ СТРУКТУРА ПРИЕМКИ ===")
pattern = r'<Документ\.ОприходованиеТоваров[^>]*>(.*?)</Документ\.ОприходованиеТоваров>'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:2000])

# Структура Инвентаризация
print("\n\n=== СТРУКТУРА ИНВЕНТАРИЗАЦИИ ===")
pattern = r'<Документ\.ИнвентаризацияТоваров[^>]*>(.*?)</Документ\.ИнвентаризацияТоваров>'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(1)[:1000])

print("\n\n=== АНАЛИЗ ЗАВЕРШЕН ===")
