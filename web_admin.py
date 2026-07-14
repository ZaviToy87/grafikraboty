# -*- coding: utf-8 -*-
"""
web_admin.py — Admin panel API
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import os
import json
from web_config import logger, get_db_connection, DATA_DIR, audit_log

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/audit-log')
def api_get_audit_log():
    """Журнал действий"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    limit = request.args.get('limit', 200, type=int)

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('''
        SELECT a.*, u.username, u.full_name
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (limit,))

    logs = [dict(row) for row in cursor.fetchall()]
    return jsonify({'status': 'success', 'items': logs})


@admin_bp.route('/telegram-seen-users')
def api_get_telegram_seen_users():
    """Участники Telegram"""
    try:
        with open(os.path.join(DATA_DIR, 'telegram_seen_users.json'), 'r', encoding='utf-8') as f:
            seen_users = json.load(f)
        return jsonify({'status': 'success', 'users': seen_users})
    except:
        return jsonify({'status': 'success', 'users': []})


@admin_bp.route('/salary-summary')
def api_get_salary_summary():
    """Перенаправление на web_api.py"""
    # Этот маршрут теперь обрабатывается в web_api.py
    from web_api import api_get_salary_summary
    return api_get_salary_summary()


@admin_bp.route('/employee-stats')
def api_get_employee_stats():
    """Перенаправление на web_api.py"""
    # Этот маршрут теперь обрабатывается в web_api.py
    from web_api import api_get_employee_stats
    return api_get_employee_stats()


@admin_bp.route('/salary-adjustments', methods=['GET', 'POST'])
def api_salary_adjustments():
    """Get or create salary adjustments (bonuses/penalties)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403

    db = get_db_connection()
    cursor = db.cursor()

    # GET - получить все надбавки за месяц
    if request.method == 'GET':
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        cursor.execute('''
            SELECT s.*, u.username, u.full_name
            FROM salary_adjustments s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.year = ? AND s.month = ?
            ORDER BY s.created_at DESC
        ''', (year, month))
        adjustments = [dict(row) for row in cursor.fetchall()]
        return jsonify({'status': 'success', 'data': adjustments})

    # POST - создать надбавку/штраф
    data = request.json or {}
    user_id = data.get('user_id')
    amount = data.get('amount')
    year = data.get('year')
    month = data.get('month')
    reason = data.get('reason', '')

    if not user_id or not amount:
        return jsonify({'status': 'error', 'message': 'user_id и amount обязательны'}), 400

    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'status': 'error', 'message': 'Пользователь не найден'}), 404

    # Сохраняем в salary_adjustments
    cursor.execute('''
        INSERT INTO salary_adjustments (user_id, year, month, amount, reason, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, year, month, float(amount), reason, session['user_id'], cursor.execute('SELECT CURRENT_TIMESTAMP')[0]))

    db.commit()

    # Запись в audit_log
    audit_log(session['user_id'], 'salary_adjustment', json.dumps({
        'user_id': user_id,
        'amount': float(amount),
        'reason': reason,
        'year': year,
        'month': month
    }))

    logger.info(f"Salary adjustment created: user_id={user_id}, amount={amount}, year={year}, month={month}")

    return jsonify({
        'status': 'success',
        'message': f'{"Бонус" if amount >= 0 else "Штраф"} создан'
    })


@admin_bp.route('/salary-adjustments/<int:adjustment_id>', methods=['DELETE'])
def api_delete_salary_adjustment(adjustment_id):
    """Delete salary adjustment"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403

    db = get_db_connection()
    cursor = db.cursor()

    # Ищем запись в salary_adjustments
    cursor.execute('SELECT * FROM salary_adjustments WHERE id = ?', (adjustment_id,))
    adjustment = cursor.fetchone()

    if not adjustment:
        return jsonify({'status': 'error', 'message': 'Надбавка не найдена'}), 404

    cursor.execute('DELETE FROM salary_adjustments WHERE id = ?', (adjustment_id,))
    db.commit()

    logger.info(f"Salary adjustment deleted: id={adjustment_id}")

    return jsonify({'status': 'success', 'message': 'Надбавка удалена'})
