with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
chunk_size = 1000

for i in range(0, len(lines), chunk_size):
    chunk = '\n'.join(lines[i:i+chunk_size])
    opens = chunk.count('{')
    closes = chunk.count('}')
    print(f'Строки {i+1}-{min(i+chunk_size, len(lines))}: {{={opens}, }}={closes}, баланс={opens-closes}')
