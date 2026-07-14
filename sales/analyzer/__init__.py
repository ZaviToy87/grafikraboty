# -*- coding: utf-8 -*-
"""
sales/analyzer/__init__.py — Анализ продаж
"""
from .parser import parse_sales_file
from .validator import validate_sales_data, SalesValidator
from .enricher import enrich_sales_data
from .metrics import calculate_metrics
from .anomaly_detector import detect_anomalies, AnomalyDetector
from .comparer import compare_periods, PeriodComparer

__all__ = [
    "parse_sales_file",
    "validate_sales_data",
    "SalesValidator",
    "enrich_sales_data",
    "calculate_metrics",
    "detect_anomalies",
    "AnomalyDetector",
    "compare_periods",
    "PeriodComparer",
]
