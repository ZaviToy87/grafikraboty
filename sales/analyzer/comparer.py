# -*- coding: utf-8 -*-
"""
sales/analyzer/comparer.py — Сравнение периодов продаж
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, datetime
from ..models.sale import Sale


class PeriodComparer:
    """Сравнение периодов продаж"""
    
    def __init__(self):
        pass
    
    def compare_periods(
        self, 
        period1_sales: List[Dict[str, Any]], 
        period2_sales: List[Dict[str, Any]],
        period1_name: str = "Текущий период",
        period2_name: str = "Предыдущий период"
    ) -> Dict[str, Any]:
        """
        Сравнить два периода продаж.
        
        Args:
            period1_sales: Продажи первого периода
            period2_sales: Продажи второго периода
            period1_name: Название первого периода
            period2_name: Название второго периода
        
        Returns:
            Словарь с результатами сравнения
        """
        # Рассчитываем метрики для каждого периода
        metrics1 = self._calculate_metrics(period1_sales)
        metrics2 = self._calculate_metrics(period2_sales)
        
        # Сравниваем
        comparison = {
            "period1": {
                "name": period1_name,
                "metrics": metrics1
            },
            "period2": {
                "name": period2_name,
                "metrics": metrics2
            },
            "changes": {}
        }
        
        # Рассчитываем изменения
        for key in metrics1:
            if key in metrics2 and isinstance(metrics1[key], (int, float)):
                val1 = metrics1[key]
                val2 = metrics2[key]
                
                if val2 > 0:
                    change_abs = val1 - val2
                    change_pct = (change_abs / val2) * 100
                else:
                    change_abs = val1 - val2
                    change_pct = 0 if val1 == 0 else 100
                
                comparison["changes"][key] = {
                    "absolute": round(change_abs, 2),
                    "percent": round(change_pct, 2),
                    "direction": "up" if change_abs > 0 else "down" if change_abs < 0 else "same",
                    "period1_value": val1,
                    "period2_value": val2
                }
        
        # Добавляем выводы
        comparison["insights"] = self._generate_insights(comparison)
        
        return comparison
    
    def _calculate_metrics(self, sales: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Рассчитать метрики для списка продаж"""
        if not sales:
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "average_check": 0.0,
                "total_items": 0,
                "unique_products": 0
            }
        
        total_revenue = 0.0
        total_items = 0
        products = set()
        
        for sale in sales:
            price = self._parse_float(sale.get('price', 0))
            qty = self._parse_int(sale.get('quantity', 1))
            
            total_revenue += price * qty
            total_items += qty
            
            product_name = sale.get('product_name', '')
            if product_name:
                products.add(product_name)
        
        total_sales = len(sales)
        average_check = total_revenue / total_sales if total_sales > 0 else 0.0
        
        return {
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "average_check": round(average_check, 2),
            "total_items": total_items,
            "unique_products": len(products)
        }
    
    def _parse_float(self, value) -> float:
        """Преобразовать в float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except ValueError:
                return 0.0
        return 0.0
    
    def _parse_int(self, value) -> int:
        """Преобразовать в int"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0
    
    def _generate_insights(self, comparison: Dict[str, Any]) -> List[str]:
        """Сгенерировать выводы на основе сравнения"""
        insights = []
        changes = comparison.get("changes", {})
        
        # Выручка
        revenue_change = changes.get("total_revenue", {})
        if revenue_change.get("direction") == "up":
            pct = revenue_change.get("percent", 0)
            insights.append(f"✅ Выручка выросла на {pct:.1f}%")
        elif revenue_change.get("direction") == "down":
            pct = abs(revenue_change.get("percent", 0))
            insights.append(f"⚠️ Выручка упала на {pct:.1f}%")
        
        # Средний чек
        check_change = changes.get("average_check", {})
        if check_change.get("direction") == "up":
            pct = check_change.get("percent", 0)
            insights.append(f"✅ Средний чек вырос на {pct:.1f}%")
        elif check_change.get("direction") == "down":
            pct = abs(check_change.get("percent", 0))
            insights.append(f"⚠️ Средний чек уменьшился на {pct:.1f}%")
        
        # Количество продаж
        sales_change = changes.get("total_sales", {})
        if sales_change.get("direction") == "up":
            pct = sales_change.get("percent", 0)
            insights.append(f"✅ Количество продаж выросло на {pct:.1f}%")
        elif sales_change.get("direction") == "down":
            pct = abs(sales_change.get("percent", 0))
            insights.append(f"⚠️ Количество продаж уменьшилось на {pct:.1f}%")
        
        # Если нет изменений
        if not insights:
            insights.append("ℹ️ Значительных изменений не обнаружено")
        
        return insights


def compare_periods(
    period1_sales: List[Dict[str, Any]], 
    period2_sales: List[Dict[str, Any]],
    period1_name: str = "Текущий период",
    period2_name: str = "Предыдущий период"
) -> Dict[str, Any]:
    """
    Сравнить два периода продаж.
    
    Args:
        period1_sales: Продажи первого периода
        period2_sales: Продажи второго периода
        period1_name: Название первого периода
        period2_name: Название второго периода
    
    Returns:
        Словарь с результатами сравнения
    """
    comparer = PeriodComparer()
    return comparer.compare_periods(
        period1_sales, 
        period2_sales, 
        period1_name, 
        period2_name
    )


if __name__ == "__main__":
    # Тест
    print("Тест сравнения периодов")
    print("=" * 50)
    
    period1 = [
        {"product_name": "Товар 1", "price": 100, "quantity": 5},
        {"product_name": "Товар 2", "price": 200, "quantity": 3},
    ]
    
    period2 = [
        {"product_name": "Товар 1", "price": 100, "quantity": 3},
        {"product_name": "Товар 2", "price": 200, "quantity": 2},
    ]
    
    result = compare_periods(period1, period2, "Январь", "Декабрь")
    
    print(f"\n{result['period1']['name']}:")
    print(f"  Выручка: {result['period1']['metrics']['total_revenue']}")
    
    print(f"\n{result['period2']['name']}:")
    print(f"  Выручка: {result['period2']['metrics']['total_revenue']}")
    
    print(f"\nИзменения:")
    for key, change in result['changes'].items():
        direction = "↑" if change['direction'] == 'up' else "↓" if change['direction'] == 'down' else "→"
        print(f"  {direction} {key}: {change['percent']:+.1f}%")
    
    print(f"\nВыводы:")
    for insight in result['insights']:
        print(f"  {insight}")
