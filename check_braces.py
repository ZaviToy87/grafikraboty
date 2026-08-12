with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
balance = 0
for i, line in enumerate(lines, 1):
    for ch in line:
        if ch == '{':
            balance += 1
        elif ch == '}':
            balance -= 1

print(f'Final balance: {balance}')
print(f'Missing closing braces: {balance}')
