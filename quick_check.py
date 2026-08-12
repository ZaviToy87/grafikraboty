with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

fetch_count = content.count('fetch(')
credentials_count = content.count('credentials')
open_braces = content.count('{')
close_braces = content.count('}')

print(f'Fetch calls: {fetch_count}')
print(f'With credentials: {credentials_count}')
print(f'Open braces: {open_braces}')
print(f'Close braces: {close_braces}')
print(f'Balanced: {open_braces == close_braces}')
print(f'Missing: {abs(open_braces - close_braces)}')
