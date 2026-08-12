# -*- coding: utf-8 -*-
"""
Добавить роут /login_vk в web_server.py
"""
with open('web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем строку с "@app.route('/login'"
insert_pos = None
for i, line in enumerate(lines):
    if "@app.route('/login'" in line and 'methods=' in line:
        insert_pos = i
        break

if insert_pos:
    # Вставляем роут перед login
    import_lines = [
        '\n',
        '@app.route("/login_vk")\n',
        'def login_vk():\n',
        '    """Страница входа с VK верификацией."""\n',
        '    return render_template("login_vk.html")\n',
        '\n',
        '\n'
    ]
    for j, imp_line in enumerate(import_lines):
        lines.insert(insert_pos + j, imp_line)
    
    with open('web_server.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f'✅ Роут /login_vk добавлен на позицию {insert_pos}')
else:
    print('❌ Не найдено место для вставки')
