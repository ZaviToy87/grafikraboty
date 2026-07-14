import sqlite3
import os
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple, List
from ..models.sale import Sale

class HistoryDB:
    def __init__(self, db_path: str = "schedule.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    total_revenue REAL NOT NULL,
                    total_quantity REAL NOT NULL,
                    item_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hash TEXT UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    unit TEXT,
                    quantity REAL NOT NULL,
                    revenue REAL NOT NULL,
                    category TEXT,
                    brand TEXT,
                    FOREIGN KEY (period_id) REFERENCES sales_periods(id)
                )
            """)
            conn.commit()

    @staticmethod
    def extract_date_from_filename(filename: str) -> Tuple[Optional[date], Optional[date]]:
        """
        Извлекает дату из имени файла:
          - продажи_2025-02-01.xlsx → (2025-02-01, 2025-02-01)
          - продажи_2025-02.xlsx → (2025-02-01, 2025-02-28)
          - продажи_2025-02-01_2025-02-05.xlsx → (2025-02-01, 2025-02-05)
        """
        import re
        from calendar import monthrange

        base = os.path.splitext(filename)[0]
        # Паттерн: YYYY-MM-DD или YYYY-MM
        match = re.search(r'(\d{4}-\d{2}-\d{2})', base)
        if match:
            d = match.group(1)
            start = date.fromisoformat(d)
            return start, start

        match = re.search(r'(\d{4}-\d{2})', base)
        if match:
            ym = match.group(1)
            year, month = map(int, ym.split('-'))
            day_start = 1
            day_end = monthrange(year, month)[1]
            start = date(year, month, day_start)
            end = date(year, month, day_end)
            return start, end

        match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})', base)
        if match:
            start = date.fromisoformat(match.group(1))
            end = date.fromisoformat(match.group(2))
            return start, end

        return None, None

    def save_period(self, filename: str, sales: List[Sale]) -> int:
        """
        Сохраняет период и все позиции.
        Возвращает period_id.
        """
        period_start, period_end = self.extract_date_from_filename(filename)
        if not period_start:
            raise ValueError(f"Не удалось определить дату из имени файла: {filename}")

        total_revenue = sum(s.revenue for s in sales)
        total_quantity = sum(s.quantity for s in sales)
        item_count = len(sales)

        # Хеш файла (для дедупликации)
        file_path = os.path.join("uploads", filename)
        hash_str = self._file_hash(file_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO sales_periods 
                    (filename, period_start, period_end, total_revenue, total_quantity, item_count, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (filename, period_start, period_end, total_revenue, total_quantity, item_count, hash_str))
                period_id = cursor.lastrowid

                for sale in sales:
                    cursor.execute("""
                        INSERT INTO sales_items 
                        (period_id, product_name, unit, quantity, revenue, category, brand)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        period_id,
                        sale.product_name,
                        sale.unit,
                        sale.quantity,
                        sale.revenue,
                        sale.category or "",
                        sale.brand or ""
                    ))
                conn.commit()
                return period_id
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"Файл уже загружен (хеш совпадает): {filename}")
                raise

    def _file_hash(self, filepath: str) -> str:
        import hashlib
        if not os.path.exists(filepath):
            return ""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get_periods(self, limit: int = 100) -> List[dict]:
        """Получает список периодов с агрегатами"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, period_start, period_end, total_revenue, total_quantity, item_count, created_at
                FROM sales_periods
                ORDER BY period_start DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "filename": r[1],
                    "period_start": r[2],
                    "period_end": r[3],
                    "total_revenue": r[4],
                    "total_quantity": r[5],
                    "item_count": r[6],
                    "created_at": r[7]
                }
                for r in rows
            ]

    def get_items_by_period(self, period_id: int) -> List[dict]:
        """Получает все позиции за период"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_name, unit, quantity, revenue, category, brand
                FROM sales_items
                WHERE period_id = ?
            """, (period_id,))
            rows = cursor.fetchall()
            return [
                {
                    "product_name": r[0],
                    "unit": r[1],
                    "quantity": r[2],
                    "revenue": r[3],
                    "category": r[4],
                    "brand": r[5]
                }
                for r in rows
            ]

    def get_daily_summary(self, start_date: date, end_date: date) -> List[dict]:
        """Агрегация по дням: выручка, количество, товары"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    DATE(sp.period_start) as day,
                    COUNT(si.id) as items,
                    SUM(si.revenue) as revenue,
                    SUM(si.quantity) as quantity
                FROM sales_periods sp
                JOIN sales_items si ON sp.id = si.period_id
                WHERE sp.period_start >= ? AND sp.period_end <= ?
                GROUP BY DATE(sp.period_start)
                ORDER BY day
            """, (start_date, end_date))
            rows = cursor.fetchall()
            return [
                {
                    "date": r[0],
                    "items": r[1],
                    "revenue": r[2],
                    "quantity": r[3]
                }
                for r in rows
            ]