# -*- coding: utf-8 -*-
"""
sales/models/report.py — Модель отчёта по продажам
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date


class Report(BaseModel):
    """Модель отчёта по продажам"""
    
    id: Optional[int] = None
    period_id: Optional[int] = None
    period_name: str = Field(..., description="Название периода")
    start_date: date = Field(..., description="Дата начала")
    end_date: date = Field(..., description="Дата окончания")
    
    # Основные метрики
    total_sales: int = Field(default=0, description="Общее количество продаж")
    total_revenue: float = Field(default=0.0, description="Общая выручка")
    total_profit: float = Field(default=0.0, description="Общая прибыль")
    average_check: float = Field(default=0.0, description="Средний чек")
    
    # Метрики по категориям
    category_metrics: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Метрики по категориям товаров"
    )
    
    # Топ товаров
    top_products: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Топ продаваемых товаров"
    )
    
    # Аномалии
    anomalies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Обнаруженные аномалии"
    )
    
    # Сравнение с предыдущим периодом
    prev_period_revenue: float = Field(default=0.0)
    revenue_change: float = Field(default=0.0)  # Процент изменения
    revenue_change_percent: str = Field(default="0%")
    
    created_at: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        """Создать Report из словаря"""
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        if "end_date" in data and isinstance(data["end_date"], str):
            data["end_date"] = date.fromisoformat(data["end_date"])
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "id": self.id,
            "period_id": self.period_id,
            "period_name": self.period_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_sales": self.total_sales,
            "total_revenue": self.total_revenue,
            "total_profit": self.total_profit,
            "average_check": self.average_check,
            "category_metrics": self.category_metrics,
            "top_products": self.top_products,
            "anomalies": self.anomalies,
            "prev_period_revenue": self.prev_period_revenue,
            "revenue_change": self.revenue_change,
            "revenue_change_percent": self.revenue_change_percent,
            "created_at": self.created_at
        }
    
    def calculate_change(self):
        """Рассчитать изменение относительно предыдущего периода"""
        if self.prev_period_revenue > 0:
            self.revenue_change = self.total_revenue - self.prev_period_revenue
            self.revenue_change_percent = f"{(self.revenue_change / self.prev_period_revenue * 100):.1f}%"
        return self
