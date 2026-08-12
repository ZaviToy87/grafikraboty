import re

def find_revision_functions():
    with open('static/js/app.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем функции связанные с ревизией
    patterns = [
        r'function openOperationModal\([^)]*\)\s*\{[^}]+?\}',
        r'function executeOperation\([^)]*\)\s*\{[^}]+?\}',
        r'function loadRevisions\([^)]*\)\s*\{[^}]+?\}',
        r'function renderRevisions\([^)]*\)\s*\{[^}]+?\}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            print(f"\n=== Найдено по шаблону: {pattern[:30]}... ===")
            for match in matches[:2]:  # Покажем первые 2 совпадения
                print(match[:500] + "..." if len(match) > 500 else match)
                print("-" * 80)
    
    # Ищем просто упоминания
    print("\n=== Поиск упоминаний 'operation' ===")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'operation' in line.lower() and 'function' in line.lower():
            print(f"Строка {i+1}: {line.strip()}")
    
    print("\n=== Поиск упоминаний 'revision' в функциях ===")
    for i, line in enumerate(lines):
        if 'revision' in line.lower() and 'function' in line.lower():
            print(f"Строка {i+1}: {line.strip()}")

if __name__ == "__main__":
    find_revision_functions()