with open('static/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_count = 0

for i, line in enumerate(lines, 1):
    # Ищем pattern: headers: { ... }, },
    if "headers: { 'Content-Type': 'application/json' }," in line:
        # Проверяем, есть ли лишняя закрывающая
        if line.count('}') > 1 or '}, },' in line or '},}' in line:
            # Исправляем
            lines[i-1] = line.replace("headers: { 'Content-Type': 'application/json' }, },", 
                                      "headers: { 'Content-Type': 'application/json' },")
            lines[i-1] = lines[i-1].replace("headers: { 'Content-Type': 'application/json' },}", 
                                            "headers: { 'Content-Type': 'application/json' },")
            fixed_count += 1
            print(f'Fixed line {i}')

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'Fixed {fixed_count} lines')

# Check balance
with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

open_b = content.count('{')
close_b = content.count('}')
print(f'Balance: {open_b} - {close_b} = {open_b - close_b}')
