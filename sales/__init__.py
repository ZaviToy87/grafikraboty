# -*- coding: utf-8 -*-
"""
sales/__init__.py — Анализ продаж ВетГид

Модуль для анализа продаж зоомагазина:
- Загрузка и парсинг данных из Excel/CSV
- Валидация данных
- Обогащение данными (категории, поставщики)
- Расчёт метрик
- Обнаружение аномалий
- Сравнение периодов
"""

__version__ = "2.0.0"

# Импорт компонентов модуля
from sales.models.sale import Sale
from sales.models.period import Period
from sales.models.report import Report
from sales.models.analysis_result import AnalysisResult
from sales.storage.local_fs import LocalStorage
from sales.storage.history_db import HistoryDB
from sales.utils.formatting import format_number, format_currency
from sales.analyzer.parser import parse_sales_file
from sales.analyzer.validator import validate_sales_data
from sales.analyzer.enricher import enrich_sales_data
from sales.analyzer.metrics import calculate_metrics
from sales.analyzer.anomaly_detector import detect_anomalies
from sales.analyzer.comparer import compare_periods

__all__ = [
    # Версия
    "__version__",
    # Модели
    "Sale",
    "Period",
    "Report",
    "AnalysisResult",
    # Хранилище
    "LocalStorage",
    "HistoryDB",
    # Утилиты
    "format_number",
    "format_currency",
    # Анализ
    "parse_sales_file",
    "validate_sales_data",
    "enrich_sales_data",
    "calculate_metrics",
    "detect_anomalies",
    "compare_periods",
]
