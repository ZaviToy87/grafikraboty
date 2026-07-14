from pydantic import BaseModel, Field
from typing import Optional, Literal
import re

class Sale(BaseModel):
    """
    Модель одной строки продажи.
    """
    id: int = Field(default_factory=lambda: hash(id))  # временный ID
    product_name: str = Field(..., description="Название товара (номенклатура)")
    unit: str = Field(default="шт.", description="Единица измерения: 'шт.', 'кг', 'уп.', etc.")
    quantity: float = Field(default=1.0, description="Количество (число)")
    revenue: float = Field(default=0.0, description="Выручка в рублях")
    category: Optional[str] = Field(None, description="Автоматически определённая категория")
    brand: Optional[str] = Field(None, description="Бренд (из названия)")
    is_new: bool = Field(False, description="Флаг: новый товар в текущем периоде")

    @staticmethod
    def clean_numeric(value: str) -> float:
        """Очищает строку числа: удаляет пробелы, заменяет ',' на '.'"""
        if not isinstance(value, str):
            value = str(value)
        # Удалить пробелы и заменить запятую на точку
        value = re.sub(r'\s+', '', value)
        value = value.replace(',', '.')
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Не удалось преобразовать '{value}' в число")

    @classmethod
    def from_raw_row(cls, row: dict, index: int):
        """
        Создаёт экземпляр Sale из сырой строки (dict с ключами как в Excel).
        Ожидает: {'Номенклатура': ..., 'Ед.': ..., 'Количество': ..., 'Выручка, ₽': ...}
        """
        try:
            product_name = str(row.get('Номенклатура', '')).strip()
            unit = str(row.get('Ед.', '')).strip()
            quantity = cls.clean_numeric(row.get('Количество', '0'))
            revenue = cls.clean_numeric(row.get('Выручка, ₽', '0'))

            return cls(
                product_name=product_name,
                unit=unit,
                quantity=quantity,
                revenue=revenue
            )
        except Exception as e:
            raise ValueError(f"Ошибка при парсинге строки {index + 1}: {e}")