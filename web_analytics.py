# -*- coding: utf-8 -*-
"""
web_analytics.py — Аналитика и дашборды
Chart.js графики: загрузка сотрудников, динамика, тепловая карта
API: /api/analytics/*
"""
from flask import Blueprint, request, jsonify, session
from web_config import get_db_connection, logger
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/employee-load')
def employee_load():
    """Загрузка сотрудников по дням недели (для графика)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Получаем всех активных сотрудников
        cursor.execute('SELECT id, full_name FROM users WHERE is_active = 1 OR is_active IS NULL')
        employees = cursor.fetchall()

        # Получаем количество смен по дням недели для каждого сотрудника
        cursor.execute('''
            SELECT u.full_name, s.day,
                   CASE CAST(strftime('%w', s.year || '-' || s.month || '-' || s.day) AS INTEGER)
                       WHEN 0 THEN 'Вс'
                       WHEN 1 THEN 'Пн'
                       WHEN 2 THEN 'Вт'
                       WHEN 3 THEN 'Ср'
                       WHEN 4 THEN 'Чт'
                       WHEN 5 THEN 'Пт'
                       WHEN 6 THEN 'Сб'
                   END as weekday
            FROM schedule s
            JOIN users u ON s.user_id = u.id
            WHERE s.year = ? AND s.month = ?
              AND s.task_ids != '[]' AND s.task_ids IS NOT NULL
            ORDER BY s.day
        ''', (year, month))

        rows = cursor.fetchall()
        db.close()

        # Группируем по сотрудникам
        employee_data = {}
        weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        weekday_counts = {w: 0 for w in weekdays}

        for emp in employees:
            name = emp['full_name'] or f"User {emp['id']}"
            employee_data[name] = {w: 0 for w in weekdays}

        for row in rows:
            name = row['full_name']
            wd = row['weekday']
            if name in employee_data and wd in employee_data[name]:
                employee_data[name][wd] += 1

        # Формируем данные для Chart.js
        labels = weekdays
        datasets = []
        colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6']

        for i, (name, counts) in enumerate(employee_data.items()):
            datasets.append({
                'label': name,
                'data': [counts[w] for w in weekdays],
                'backgroundColor': colors[i % len(colors)],
                'borderColor': colors[i % len(colors)],
                'borderWidth': 2,
                'tension': 0.3
            })

        return jsonify({
            'status': 'success',
            'labels': labels,
            'datasets': datasets
        })

    except Exception as e:
        logger.error(f"Error in employee_load: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/dynamics')
def dynamics():
    """Динамика операций по дням месяца"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Операции с товарами (из revision_transactions)
        cursor.execute('''
            SELECT CAST(strftime('%d', created_at) AS INTEGER) as day,
                   COUNT(*) as count,
                   action
            FROM revision_transactions
            WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
              AND CAST(strftime('%m', created_at) AS INTEGER) = ?
            GROUP BY day, action
            ORDER BY day
        ''', (year, month))

        rows = cursor.fetchall()

        # Дни месяца
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        days = list(range(1, days_in_month + 1))

        # Группируем по типам операций
        action_types = ['sold', 'sold_discount', 'written_off_expired', 'written_off_damaged', 'taken_personal']
        action_labels = {
            'sold': 'Продажи',
            'sold_discount': 'Продажи со скидкой',
            'written_off_expired': 'Списание (просрочка)',
            'written_off_damaged': 'Списание (повреждение)',
            'taken_personal': 'Личное использование'
        }
        action_colors = {
            'sold': '#10b981',
            'sold_discount': '#f59e0b',
            'written_off_expired': '#ef4444',
            'written_off_damaged': '#f97316',
            'taken_personal': '#8b5cf6'
        }

        action_data = {a: {d: 0 for d in days} for a in action_types}
        for row in rows:
            day = row['day']
            action = row['action']
            count = row['count']
            if action in action_data and day in action_data[action]:
                action_data[action][day] = count

        datasets = []
        for action in action_types:
            if any(action_data[action].values()):
                datasets.append({
                    'label': action_labels.get(action, action),
                    'data': [action_data[action][d] for d in days],
                    'backgroundColor': action_colors.get(action, '#6366f1'),
                    'borderColor': action_colors.get(action, '#6366f1'),
                    'borderWidth': 2,
                    'tension': 0.3,
                    'fill': False
                })

        db.close()

        return jsonify({
            'status': 'success',
            'labels': [str(d) for d in days],
            'datasets': datasets
        })

    except Exception as e:
        logger.error(f"Error in dynamics: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/heatmap')
def heatmap():
    """Тепловая карта активности по часам и дням недели"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Получаем операции сгруппированные по часу и дню недели
        cursor.execute('''
            SELECT CAST(strftime('%w', created_at) AS INTEGER) as weekday,
                   CAST(strftime('%H', created_at) AS INTEGER) as hour,
                   COUNT(*) as count
            FROM revision_transactions
            WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
              AND CAST(strftime('%m', created_at) AS INTEGER) = ?
            GROUP BY weekday, hour
            ORDER BY weekday, hour
        ''', (year, month))

        rows = cursor.fetchall()
        db.close()

        # Матрица 7x24 (дни недели x часы)
        weekdays = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
        hours = list(range(24))

        matrix = [[0 for _ in hours] for _ in weekdays]
        max_val = 0

        for row in rows:
            wd = row['weekday']
            h = row['hour']
            c = row['count']
            if 0 <= wd < 7 and 0 <= h < 24:
                matrix[wd][h] = c
                if c > max_val:
                    max_val = c

        return jsonify({
            'status': 'success',
            'weekdays': weekdays,
            'hours': hours,
            'matrix': matrix,
            'max_value': max_val
        })

    except Exception as e:
        logger.error(f"Error in heatmap: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/summary')
def summary():
    """Сводная статистика для дашборда"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    try:
        db = get_db_connection()
        cursor = db.cursor()

        now = datetime.now()
        year = now.year
        month = now.month

        # Активные сотрудники
        cursor.execute('SELECT COUNT(*) as cnt FROM users WHERE is_active = 1 OR is_active IS NULL')
        total_employees = cursor.fetchone()['cnt']

        # Смены в этом месяце
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id || '-' || day) as cnt
            FROM schedule
            WHERE year = ? AND month = ? AND task_ids != '[]' AND task_ids IS NOT NULL
        ''', (year, month))
        total_shifts = cursor.fetchone()['cnt']

        # Операции за месяц
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM revision_transactions
            WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
              AND CAST(strftime('%m', created_at) AS INTEGER) = ?
        ''', (year, month))
        total_operations = cursor.fetchone()['cnt']

        # Продажи за месяц
        cursor.execute('''
            SELECT COUNT(*) as cnt, COALESCE(SUM(price_with_discount), 0) as total
            FROM revision_transactions
            WHERE action IN ('sold', 'sold_discount', 'sold_promo')
              AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
              AND CAST(strftime('%m', created_at) AS INTEGER) = ?
        ''', (year, month))
        sales_row = cursor.fetchone()
        total_sales = sales_row['cnt']
        total_revenue = sales_row['total']

        # Списания за месяц
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM revision_transactions
            WHERE action LIKE 'written_off%'
              AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
              AND CAST(strftime('%m', created_at) AS INTEGER) = ?
        ''', (year, month))
        total_writeoffs = cursor.fetchone()['cnt']

        db.close()

        return jsonify({
            'status': 'success',
            'summary': {
                'total_employees': total_employees,
                'total_shifts': total_shifts,
                'total_operations': total_operations,
                'total_sales': total_sales,
                'total_revenue': float(total_revenue),
                'total_writeoffs': total_writeoffs,
                'year': year,
                'month': month
            }
        })

    except Exception as e:
        logger.error(f"Error in summary: {e}")
        return jsonify({'error': str(e)}), 500
