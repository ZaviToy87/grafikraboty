# -*- coding: utf-8 -*-
"""
sales/web/__init__.py — Веб-интерфейс анализа продаж
"""
from .routes import init_sales_routes, bp

__all__ = ["init_sales_routes", "bp"]
