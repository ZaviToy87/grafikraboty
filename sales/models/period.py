# -*- coding: utf-8 -*-
"""
sales/models/period.py — Модель периода для анализа продаж
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class Period(BaseModel):
    """Модель периода анализа продаж"""
    
    id: Optional[int] = None
    name: str = Field(..., description="Название периода (например, 'Январь 2024')")
    start_date: date = Field(..., description="Дата начала периода")
    end_date: date = Field(..., description="Дата окончания периода")
    is_active: bool = Field(default=True, description="Активен ли период")
    created_at: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Period":
        """Создать Period из словаря"""
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        if "end_date" in data and isinstance(data["end_date"], str):
            data["end_date"] = date.fromisoformat(data["end_date"])
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
    
    @property
    def duration_days(self) -> int:
        """Количество дней в периоде"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
