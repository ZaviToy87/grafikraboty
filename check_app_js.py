import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

open_braces = content.count('{')
close_braces = content.count('}')
print(f'Open braces: {open_braces}')
print(f'Close braces: {close_braces}')
print(f'Balanced: {open_braces == close_braces}')

matches = re.findall(r"fetch\([^)]+credentials:\s*'include'", content)
print(f'Fetch with credentials: {len(matches)}')

# Проверяем первую строку с fetch
for i, line in enumerate(content.split('\n')[:100], 1):
    if 'fetch(' in line and 'credentials' not in line:
        print(f'Line {i} may need credentials: {line[:80]}...')
        break
