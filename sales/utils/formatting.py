import re
from typing import Union

def parse_numeric(value: Union[str, float, int]) -> float:
    """
    Безопасно парсит число из строки с поддержкой:
      - '1 234,56' → 1234.56
      - '1,234' → 1.234
      - '1234' → 1234.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise ValueError(f"Ожидалась строка, получено: {type(value)}")

    # Удаляем все пробелы и заменяем запятую на точку
    value = re.sub(r'\s+', '', value)
    value = value.replace(',', '.')
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Не удалось распознать число: '{value}'")

def format_number(num: float, decimal_places: int = 2) -> str:
    """Форматирует число как '1 234,56'"""
    if num is None:
        return ""
    s = f"{num:.{decimal_places}f}"
    parts = s.split('.')
    integer_part = parts[0]
    fractional_part = parts[1] if len(parts) > 1 else ""
    # Добавляем пробелы каждые 3 цифры справа налево
    integer_part = re.sub(r'(\d)(?=(\d{3})+(?!\d))', r'\1 ', integer_part)
    if fractional_part:
        return f"{integer_part},{fractional_part}"
    return integer_part

def format_currency(amount: float) -> str:
    """Форматирует сумму в рублях: '1 234,56 ₽'"""
    return f"{format_number(amount)} ₽"