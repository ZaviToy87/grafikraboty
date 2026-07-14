# -*- coding: utf-8 -*-
"""
sales/analyzer/anomaly_detector.py — Обнаружение аномалий в продажах
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
import statistics


class AnomalyDetector:
    """Детектор аномалий в данных о продажах"""
    
    def __init__(self, z_threshold: float = 2.5):
        """
        Инициализировать детектор.
        
        Args:
            z_threshold: Порог Z-score для обнаружения аномалий
        """
        self.z_threshold = z_threshold
    
    def detect_anomalies(self, sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обнаружить аномалии в данных о продажах.
        
        Args:
            sales: Список записей о продажах
        
        Returns:
            Список обнаруженных аномалий
        """
        anomalies = []
        
        # Извлекаем цены и количества
        prices = []
        quantities = []
        daily_revenue = {}
        
        for sale in sales:
            price = self._parse_float(sale.get('price', 0))
            qty = self._parse_int(sale.get('quantity', 1))
            
            if price > 0:
                prices.append(price)
            if qty > 0:
                quantities.append(qty)
            
            # Группируем по датам
            sale_date = sale.get('sale_date', str(date.today()))
            if sale_date not in daily_revenue:
                daily_revenue[sale_date] = 0
            daily_revenue[sale_date] += price * qty
        
        # Обнаруживаем аномалии в ценах
        price_anomalies = self._find_statistical_anomalies(
            prices, "price", self.z_threshold
        )
        anomalies.extend(price_anomalies)
        
        # Обнаруживаем аномалии в количествах
        qty_anomalies = self._find_statistical_anomalies(
            quantities, "quantity", self.z_threshold
        )
        anomalies.extend(qty_anomalies)
        
        # Обнаруживаем аномалии в ежедневной выручке
        revenue_values = list(daily_revenue.values())
        revenue_anomalies = self._find_statistical_anomalies(
            revenue_values, "daily_revenue", self.z_threshold,
            extra_data={"by_date": daily_revenue}
        )
        anomalies.extend(revenue_anomalies)
        
        # Проверяем на нулевые продажи
        zero_anomalies = self._check_zero_sales(sales)
        anomalies.extend(zero_anomalies)
        
        # Проверяем на дубликаты
        duplicate_anomalies = self._check_duplicates(sales)
        anomalies.extend(duplicate_anomalies)
        
        return anomalies
    
    def _parse_float(self, value) -> float:
        """Преобразовать значение в float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except ValueError:
                return 0.0
        return 0.0
    
    def _parse_int(self, value) -> int:
        """Преобразовать значение в int"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0
    
    def _find_statistical_anomalies(
        self, 
        values: List[float], 
        field_name: str,
        z_threshold: float,
        extra_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Найти статистические аномалии используя Z-score.
        
        Args:
            values: Список значений
            field_name: Имя поля для отчёта
            z_threshold: Порог Z-score
            extra_data: Дополнительные данные
        
        Returns:
            Список аномалий
        """
        anomalies = []
        
        if len(values) < 3:
            return anomalies
        
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        
        if stdev == 0:
            return anomalies
        
        for i, value in enumerate(values):
            z_score = (value - mean) / stdev
            
            if abs(z_score) > z_threshold:
                anomaly = {
                    "type": "statistical_outlier",
                    "field": field_name,
                    "value": value,
                    "z_score": round(z_score, 2),
                    "mean": round(mean, 2),
                    "stdev": round(stdev, 2),
                    "severity": "high" if abs(z_score) > 4 else "medium",
                    "description": f"Значение {value} отклоняется от среднего ({mean}) на {abs(z_score):.1f} стандартных отклонений"
                }
                
                if extra_data:
                    anomaly["details"] = extra_data
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _check_zero_sales(self, sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Проверить на продажи с нулевой ценой"""
        anomalies = []
        
        for i, sale in enumerate(sales):
            price = self._parse_float(sale.get('price', 0))
            if price == 0:
                anomalies.append({
                    "type": "zero_price",
                    "field": "price",
                    "value": 0,
                    "row": i,
                    "severity": "medium",
                    "description": f"Продажа с нулевой ценой: {sale.get('product_name', 'Неизвестный товар')}"
                })
        
        return anomalies
    
    def _check_duplicates(self, sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Проверить на дубликаты продаж"""
        anomalies = []
        seen = {}
        
        for i, sale in enumerate(sales):
            # Создаём ключ для идентификации дубликата
            key = (
                sale.get('product_name', ''),
                str(sale.get('price', '')),
                str(sale.get('sale_date', ''))
            )
            
            if key in seen:
                anomalies.append({
                    "type": "duplicate_sale",
                    "field": "multiple",
                    "rows": [seen[key], i],
                    "severity": "low",
                    "description": f"Возможный дубликат продажи: {sale.get('product_name', 'Неизвестный товар')}"
                })
            else:
                seen[key] = i
        
        return anomalies
    
    def get_summary(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Получить сводку по аномалиям.
        
        Args:
            anomalies: Список аномалий
        
        Returns:
            Словарь со сводкой
        """
        summary = {
            "total_anomalies": len(anomalies),
            "by_type": {},
            "by_severity": {"high": 0, "medium": 0, "low": 0}
        }
        
        for anomaly in anomalies:
            atype = anomaly.get("type", "unknown")
            severity = anomaly.get("severity", "low")
            
            summary["by_type"][atype] = summary["by_type"].get(atype, 0) + 1
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        return summary


def detect_anomalies(sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Обнаружить аномалии в данных о продажах.
    
    Args:
        sales: Список записей о продажах
    
    Returns:
        Список обнаруженных аномалий
    """
    detector = AnomalyDetector()
    return detector.detect_anomalies(sales)


if __name__ == "__main__":
    # Тест
    print("Тест детектора аномалий")
    print("=" * 50)
    
    test_sales = [
        {"product_name": "Товар 1", "price": 100, "quantity": 2},
        {"product_name": "Товар 2", "price": 105, "quantity": 1},
        {"product_name": "Товар 3", "price": 98, "quantity": 3},
        {"product_name": "Товар 4", "price": 1000, "quantity": 1},  # Аномалия!
        {"product_name": "Товар 5", "price": 0, "quantity": 1},  # Нулевая цена
    ]
    
    anomalies = detect_anomalies(test_sales)
    print(f"Найдено аномалий: {len(anomalies)}")
    for a in anomalies:
        print(f"  • {a['type']}: {a['description']}")
