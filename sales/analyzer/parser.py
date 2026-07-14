import pandas as pd
import os
from pathlib import Path
from .validator import validate_sales_data
from ..models.sale import Sale

def parse_sales_file(file_path: str, filename: str = "") -> list[Sale]:
    """
    Парсит файл продаж (XLSX или CSV) в список объектов Sale.
    Поддерживает ваш формат:
      - Строка 0: заголовки ('Покупатель', '', 'Количество', 'Выручка, ₽')
      - Строка 1: подзаголовки ('Номенклатура', 'Ед.', '', '')
      - Строка 2+: данные
      - Последняя строка: 'Итого'

    Возвращает список Sale, исключая итоговую строку.
    """
    path = Path(file_path)
    if path.suffix.lower() == '.xlsx':
        # Читаем без заголовков — чтобы не потерять структуру
        df = pd.read_excel(path, header=None, dtype=str)
    elif path.suffix.lower() == '.csv':
        df = pd.read_csv(path, header=None, dtype=str)
    else:
        raise ValueError(f"Поддерживаемые форматы: .xlsx, .csv. Получен: {path.suffix}")

    # Удаляем пустые строки и столбцы
    df = df.dropna(how='all').dropna(axis=1, how='all')

    # Определяем индексы колонок по содержимому первой строки
    headers = df.iloc[0].fillna('').astype(str).str.strip().tolist()
    subheaders = df.iloc[1].fillna('').astype(str).str.strip().tolist()

    # Ищем колонки по ключевым словам
    col_product = None
    col_unit = None
    col_quantity = None
    col_revenue = None

    for i, h in enumerate(headers):
        if 'номенклатура' in h.lower():
            col_product = i
        elif 'ед' in h.lower():
            col_unit = i
        elif 'количество' in h.lower():
            col_quantity = i
        elif 'выручка' in h.lower() and '₽' in h:
            col_revenue = i

    # Если не нашли по заголовкам — пробуем по подзаголовкам
    if col_product is None and 'номенклатура' in subheaders:
        col_product = subheaders.index('номенклатура')
    if col_unit is None:
        for i, sh in enumerate(subheaders):
            if 'ед.' in sh.lower() or 'ед' in sh.lower():
                col_unit = i
                break
    if col_quantity is None:
        for i, h in enumerate(headers):
            if 'количество' in h.lower():
                col_quantity = i
                break
    if col_revenue is None:
        for i, h in enumerate(headers):
            if 'выручка' in h.lower() and ('₽' in h or 'руб' in h.lower()):
                col_revenue = i
                break

    if None in [col_product, col_unit, col_quantity, col_revenue]:
        raise ValueError(f"Не удалось определить колонки. Заголовки: {headers}, подзаголовки: {subheaders}")

    # Извлекаем данные (начиная с строки 2, до строки с 'Итого')
    sales = []
    for idx, row in df.iterrows():
        if idx < 2:
            continue
        # Пропускаем строку "Итого"
        if isinstance(row[col_product], str) and 'итого' in row[col_product].lower():
            break

        raw_row = {
            'Номенклатура': row[col_product],
            'Ед.': row[col_unit],
            'Количество': row[col_quantity],
            'Выручка, ₽': row[col_revenue]
        }
        try:
            sale = Sale.from_raw_row(raw_row, idx)
            sales.append(sale)
        except Exception as e:
            print(f"⚠️ Пропущена строка {idx + 1}: {e}")
            continue

    # Валидация
    validate_sales_data(sales)

    return sales