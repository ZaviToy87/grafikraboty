# -*- coding: utf-8 -*-
"""
sales/models/analysis_result.py — Результат анализа продаж
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime


class AnalysisResult(BaseModel):
    """Модель результата анализа продаж"""
    
    id: Optional[int] = None
    
    # Период анализа
    period_name: str = Field(..., description="Название периода")
    start_date: date = Field(..., description="Дата начала")
    end_date: date = Field(..., description="Дата окончания")
    
    # Статистика
    total_records: int = Field(default=0, description="Всего записей")
    valid_records: int = Field(default=0, description="Валидных записей")
    invalid_records: int = Field(default=0, description="Невалидных записей")
    
    # Финансовые показатели
    total_revenue: float = Field(default=0.0, description="Общая выручка")
    total_profit: float = Field(default=0.0, description="Общая прибыль")
    average_check: float = Field(default=0.0, description="Средний чек")
    min_check: float = Field(default=0.0, description="Минимальный чек")
    max_check: float = Field(default=0.0, description="Максимальный чек")
    
    # По категориям
    by_category: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Статистика по категориям"
    )
    
    # По датам
    by_date: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Статистика по датам"
    )
    
    # Топ товаров
    top_products: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Топ-10 продаваемых товаров"
    )
    
    # Аномалии
    anomalies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Обнаруженные аномалии"
    )
    
    # Ошибки валидации
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Ошибки валидации данных"
    )
    
    # Метаданные
    analyzed_at: Optional[str] = None
    analysis_duration_ms: float = Field(default=0.0)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisResult":
        """Создать AnalysisResult из словаря"""
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        if "end_date" in data and isinstance(data["end_date"], str):
            data["end_date"] = date.fromisoformat(data["end_date"])
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "id": self.id,
            "period_name": self.period_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "total_revenue": self.total_revenue,
            "total_profit": self.total_profit,
            "average_check": self.average_check,
            "min_check": self.min_check,
            "max_check": self.max_check,
            "by_category": self.by_category,
            "by_date": self.by_date,
            "top_products": self.top_products,
            "anomalies": self.anomalies,
            "validation_errors": self.validation_errors,
            "analyzed_at": self.analyzed_at,
            "analysis_duration_ms": self.analysis_duration_ms
        }
    
    def add_anomaly(self, anomaly_type: str, description: str, 
                    severity: str = "medium", **kwargs):
        """Добавить аномалию"""
        self.anomalies.append({
            "type": anomaly_type,
            "description": description,
            "severity": severity,
            "details": kwargs,
            "detected_at": datetime.now().isoformat()
        })
        return self
    
    def add_validation_error(self, field: str, value: Any, 
                             error: str, row: int = None):
        """Добавить ошибку валидации"""
        self.validation_errors.append({
            "field": field,
            "value": str(value),
            "error": error,
            "row": row,
            "detected_at": datetime.now().isoformat()
        })
        self.invalid_records += 1
        return self
