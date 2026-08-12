with open('static/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Строки где } больше чем { ===\n")

for i, line in enumerate(lines, 1):
    opens = line.count('{')
    closes = line.count('}')
    if closes > opens:
        diff = closes - opens
        print(f"{i}: +{diff} : {line.rstrip()[:100]}")
