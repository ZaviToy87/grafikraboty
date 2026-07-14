# -*- coding: utf-8 -*-
"""
sales/analyzer/validator.py — Валидация данных о продажах
"""
import re
from typing import List, Tuple, Dict, Any, Optional
from ..models.sale import Sale
from ..models.analysis_result import AnalysisResult


class SalesValidator:
    """Валидатор данных о продажах"""
    
    # Паттерны для валидации
    BARCODE_PATTERN = re.compile(r'^\d{8,14}$')  # Штрих-код 8-14 цифр
    PRICE_PATTERN = re.compile(r'^\d+([.,]\d{1,2})?$')  # Цена с 1-2 знаками после запятой
    QUANTITY_PATTERN = re.compile(r'^\d+$')  # Количество - целое число
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_sale(self, sale: Sale) -> Tuple[bool, List[str]]:
        """
        Валидировать одну запись о продаже.
        
        Args:
            sale: Объект Sale для валидации
        
        Returns:
            (is_valid, список ошибок)
        """
        self.errors = []
        self.warnings = []
        
        # Проверка обязательных полей
        self._check_required_fields(sale)
        
        # Проверка типов данных
        self._check_field_types(sale)
        
        # Проверка диапазонов
        self._check_ranges(sale)
        
        # Проверка штрих-кода
        self._validate_barcode(sale)
        
        # Проверка цены
        self._validate_price(sale)
        
        # Проверка количества
        self._validate_quantity(sale)
        
        # Проверка даты
        self._validate_date(sale)
        
        return len(self.errors) == 0, self.errors
    
    def _check_required_fields(self, sale: Sale):
        """Проверка обязательных полей"""
        required = ['product_name', 'price']
        for field in required:
            value = getattr(sale, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                self.errors.append(f"Обязательное поле '{field}' отсутствует")
    
    def _check_field_types(self, sale: Sale):
        """Проверка типов данных полей"""
        if hasattr(sale, 'price') and sale.price is not None:
            if not isinstance(sale.price, (int, float, str)):
                self.errors.append(f"Цена должна быть числом или строкой, получено {type(sale.price)}")
        
        if hasattr(sale, 'quantity') and sale.quantity is not None:
            if not isinstance(sale.quantity, (int, str)):
                self.errors.append(f"Количество должно быть целым числом, получено {type(sale.quantity)}")
    
    def _check_ranges(self, sale: Sale):
        """Проверка диапазонов значений"""
        if hasattr(sale, 'price') and sale.price is not None:
            try:
                price = float(sale.price) if isinstance(sale.price, str) else sale.price
                if price < 0:
                    self.errors.append(f"Цена не может быть отрицательной: {price}")
                elif price > 1_000_000:
                    self.warnings.append(f"Подозрительно высокая цена: {price}")
            except (ValueError, TypeError):
                pass
        
        if hasattr(sale, 'quantity') and sale.quantity is not None:
            try:
                qty = int(sale.quantity) if isinstance(sale.quantity, str) else sale.quantity
                if qty < 0:
                    self.errors.append(f"Количество не может быть отрицательным: {qty}")
                elif qty > 10000:
                    self.warnings.append(f"Подозрительно большое количество: {qty}")
            except (ValueError, TypeError):
                pass
    
    def _validate_barcode(self, sale: Sale):
        """Валидация штрих-кода"""
        if hasattr(sale, 'barcode') and sale.barcode:
            barcode_str = str(sale.barcode).strip()
            if not self.BARCODE_PATTERN.match(barcode_str.replace('-', '')):
                self.warnings.append(f"Подозрительный штрих-код: {sale.barcode}")
    
    def _validate_price(self, sale: Sale):
        """Валидация цены"""
        if hasattr(sale, 'price') and sale.price is not None:
            price_str = str(sale.price).strip()
            if not self.PRICE_PATTERN.match(price_str):
                self.errors.append(f"Некорректный формат цены: {sale.price}")
    
    def _validate_quantity(self, sale: Sale):
        """Валидация количества"""
        if hasattr(sale, 'quantity') and sale.quantity is not None:
            qty_str = str(sale.quantity).strip()
            if not self.QUANTITY_PATTERN.match(qty_str):
                self.errors.append(f"Некорректный формат количества: {sale.quantity}")
    
    def _validate_date(self, sale: Sale):
        """Валидация даты продажи"""
        if hasattr(sale, 'sale_date') and sale.sale_date:
            # Дата уже должна быть валидной если это date/datetime объект
            pass
    
    def validate_batch(self, sales: List[Sale]) -> AnalysisResult:
        """
        Валидировать пакет записей о продажах.
        
        Args:
            sales: Список записей для валидации
        
        Returns:
            AnalysisResult с результатами валидации
        """
        from datetime import date
        from ..models.analysis_result import AnalysisResult
        
        result = AnalysisResult(
            period_name="Валидация",
            start_date=date.today(),
            end_date=date.today(),
            total_records=len(sales)
        )
        
        for i, sale in enumerate(sales):
            is_valid, errors = self.validate_sale(sale)
            if is_valid:
                result.valid_records += 1
            else:
                for error in errors:
                    result.add_validation_error(
                        field="multiple",
                        value=str(sale),
                        error=error,
                        row=i
                    )
        
        return result


def validate_sales_data(sales: List[Sale]) -> Tuple[List[Sale], List[Dict[str, Any]]]:
    """
    Валидировать данные о продажах.
    
    Args:
        sales: Список записей для валидации
    
    Returns:
        (валидные записи, список ошибок)
    """
    validator = SalesValidator()
    valid_sales = []
    all_errors = []
    
    for i, sale in enumerate(sales):
        is_valid, errors = validator.validate_sale(sale)
        if is_valid:
            valid_sales.append(sale)
        else:
            for error in errors:
                all_errors.append({
                    "row": i,
                    "error": error,
                    "data": str(sale)
                })
    
    return valid_sales, all_errors


if __name__ == "__main__":
    # Тест
    print("Тест валидатора продаж")
    print("=" * 50)
    
    # Создаём тестовые данные
    test_sales = [
        Sale(product_name="Товар 1", price=100.50, quantity=2),
        Sale(product_name="Товар 2", price=-50),  # Ошибка: отрицательная цена
        Sale(product_name="", price=100),  # Ошибка: пустое название
    ]
    
    valid, errors = validate_sales_data(test_sales)
    print(f"Валидно: {len(valid)}, Ошибок: {len(errors)}")
    for err in errors:
        print(f"  - {err}")
