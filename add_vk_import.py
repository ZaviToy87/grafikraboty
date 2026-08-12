# -*- coding: utf-8 -*-
"""
Скрипт для добавления импорта vk_verification в web_server.py
"""
with open('web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем строку с "def get_db_connection"
insert_pos = None
for i, line in enumerate(lines):
    if 'def get_db_connection' in line:
        insert_pos = i
        break

if insert_pos:
    # Вставляем импорт перед функцией
    import_lines = [
        '# VK верификация\n',
        'try:\n',
        '    import vk_verification\n',
        '    VK_VERIFICATION_AVAILABLE = True\n',
        'except ImportError:\n',
        '    VK_VERIFICATION_AVAILABLE = False\n',
        '    vk_verification = None\n',
        '\n',
        '\n'
    ]
    for j, imp_line in enumerate(import_lines):
        lines.insert(insert_pos + j, imp_line)
    
    with open('web_server.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f'✅ Импорт добавлен на позицию {insert_pos}')
else:
    print('❌ Не найдено место для вставки')
