# -*- coding: utf-8 -*-
"""
sales/storage/__init__.py — Хранилище данных
"""
from .local_fs import LocalStorage
from .history_db import HistoryDB

__all__ = ["LocalStorage", "HistoryDB"]
