from openpyxl import load_workbook

wb = load_workbook('НОМЕНКЛАТУРА И ЦЕНА.xlsx', data_only=True)
ws = wb.active

print("Проверка Excel файла:")
print(f"Размеры: {ws.max_row} x {ws.max_column}")

count = 0
prices = 0

for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    name = row[0] if len(row) > 0 and row[0] else None
    price = row[5] if len(row) > 5 and row[5] else 0
    
    if name:
        count += 1
    if price:
        prices += 1
    
    print(f'Строка {i}: {name[:50] if name else "None"}, цена: {price}')
    
    if i >= 10:
        break

print(f'\nВсего строк с именем: {count}')
print(f'Всего строк с ценой: {prices}')

wb.close()
