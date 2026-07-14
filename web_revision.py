# -*- coding: utf-8 -*-
"""
web_revision.py — Модуль ревизии товаров с истекающим сроком годности
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import sqlite3
import json
from web_config import logger, get_db_connection
import vk_bot

revision_bp = Blueprint('revision', __name__)

# Регламент уценки (в днях)
DISCOUNT_RULES = [
    {'days': 30, 'percent': 40},    # ≤ 1 месяца
    {'days': 60, 'percent': 35},    # ≤ 2 месяцев
    {'days': 90, 'percent': 25},    # ≤ 3 месяцев
    {'days': 120, 'percent': 15},   # ≤ 4 месяцев
]

EXPIRED_DISCOUNT = 50  # Срок истёк


def log_revision_action(revision_id, user_id, full_name, action, old_value=None, new_value=None):
    """Записать действие в лог аудита"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO revision_audit_log
            (revision_id, user_id, full_name, action, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (revision_id, user_id, full_name, action, 
              json.dumps(old_value) if old_value else None,
              json.dumps(new_value) if new_value else None))
        db.commit()
        db.close()
        logger.info(f"Audit log: {action} by {full_name} (revision {revision_id})")
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")


def calculate_discount(expiry_date_str):
    """
    Рассчитать скидку на основе остатка времени до срока годности
    Возвращает: (days_remaining, discount_percent, status_text)
    """
    try:
        expiry = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        delta = expiry - today
        days_remaining = delta.days
        
        if days_remaining < 0:
            # Срок истёк
            return days_remaining, EXPIRED_DISCOUNT, 'expired'
        
        # Проверяем правила уценки
        for rule in DISCOUNT_RULES:
            if days_remaining <= rule['days']:
                return days_remaining, rule['percent'], 'discount'
        
        # Больше 4 месяцев — без скидки
        return days_remaining, 0, 'normal'
        
    except Exception as e:
        logger.error(f"Error calculating discount: {e}")
        return None, 0, 'error'


def format_days_remaining(days):
    """Форматировать остаток дней в человекочитаемый вид"""
    if days is None:
        return '—'
    if days < 0:
        return f'Просрочено {abs(days)} дн.'
    if days == 0:
        return 'Истекает сегодня'
    if days == 1:
        return '1 день'
    if days < 30:
        return f'{days} дн.'
    
    months = days // 30
    remaining_days = days % 30
    
    result = []
    if months > 0:
        result.append(f'{months} мес.')
    if remaining_days > 0:
        result.append(f'{remaining_days} дн.')
    
    return ' '.join(result)


@revision_bp.route('/revisions', methods=['GET'])
def get_revisions():
    """Получить список товаров на ревизии"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    user_id = session['user_id']
    role = session.get('role', 'employee')

    filter_type = request.args.get('filter', 'all')  # all, my, decision, archive
    search = request.args.get('search', '')  # Поиск по названию или штрих-коду
    sort_by = request.args.get('sort', 'expiry_date')  # expiry_date, created_at, name, discount

    db = get_db_connection()
    cursor = db.cursor()

    # Базовый запрос
    base_query = '''
        SELECT * FROM product_revisions
    '''

    conditions = []
    params = []

    # Все видят ВСЕ товары (сотрудники тоже)
    if filter_type == 'my':
        conditions.append('user_id = ?')
        params.append(user_id)
    elif filter_type == 'decision':
        conditions.append('status = ?')
        params.append('admin_decision')
    elif filter_type == 'active':
        conditions.append('status IN (?, ?)')
        params.append('active')
        params.append('admin_decision')
    elif filter_type == 'archive':
        conditions.append('status IN (?, ?, ?)')
        params.extend(['sold', 'utilized', 'reserved_admin'])

    # Поиск по названию или штрих-коду (регистронезависимо через Python)
    if search:
        # Загружаем все и фильтруем в Python (как в штрих-кодах)
        pass  # Обработаем ниже

    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)

    # Сортировка
    if sort_by == 'created_at':
        base_query += ' ORDER BY created_at DESC, id DESC'  # Новые первыми
    elif sort_by == 'name':
        base_query += ' ORDER BY product_name ASC'
    elif sort_by == 'discount':
        base_query += ' ORDER BY discount_percent DESC, days_remaining ASC'
    else:  # expiry_date (по умолчанию)
        base_query += ' ORDER BY expiry_date ASC, created_at DESC'

    logger.info(f"Revision query: {base_query}")
    logger.info(f"Revision params: {params}")

    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    revisions = []
    for row in rows:
        rev = dict(row)
        rev['days_remaining_formatted'] = format_days_remaining(rev['days_remaining'])

        # Цветовой статус для UI
        if rev['days_remaining'] is not None and rev['days_remaining'] < 0:
            rev['color_status'] = 'red'
        elif rev['discount_percent'] and rev['discount_percent'] >= 40:
            rev['color_status'] = 'orange'
        elif rev['discount_percent'] and rev['discount_percent'] >= 25:
            rev['color_status'] = 'yellow'
        else:
            rev['color_status'] = 'green'

        revisions.append(rev)

    # Фильтрация поиска в Python (как в штрих-кодах для кириллицы)
    if search:
        search_lower = search.lower()
        revisions = [
            rev for rev in revisions
            if search_lower in rev['product_name'].lower() or
               (rev['barcode'] and search_lower in str(rev['barcode']).lower())
        ]

    logger.info(f"Revision loaded: {len(revisions)} items for user {user_id} (role={role}, filter={filter_type}, search={search})")

    return jsonify({'status': 'success', 'revisions': revisions})


@revision_bp.route('/revisions', methods=['POST'])
def create_revision():
    """Добавить товар на ревизию"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}

    product_name = data.get('product_name', '').strip()
    retail_price = data.get('retail_price')
    expiry_date = data.get('expiry_date')
    barcode = data.get('barcode', '').strip()
    quantity = int(data.get('quantity', 1)) if data.get('quantity') else 1

    if not product_name:
        return jsonify({'status': 'error', 'message': 'Название товара обязательно'}), 400

    if retail_price is None or retail_price <= 0:
        return jsonify({'status': 'error', 'message': 'Укажите корректную цену'}), 400

    if not expiry_date:
        return jsonify({'status': 'error', 'message': 'Укажите срок годности'}), 400
    
    # Рассчитываем скидку
    days_remaining, discount_percent, status = calculate_discount(expiry_date)
    final_price = retail_price * (1 - discount_percent / 100)
    
    # Определяем статус
    if days_remaining < 0:
        db_status = 'admin_decision'  # Требует решения админа
    else:
        db_status = 'active'
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO product_revisions
        (user_id, full_name, product_name, retail_price, expiry_date, barcode, quantity,
         days_remaining, discount_percent, final_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        session['full_name'],
        product_name,
        retail_price,
        expiry_date,
        barcode,
        quantity,  # Добавляем количество
        days_remaining,
        discount_percent,
        final_price,
        db_status
    ))
    
    db.commit()
    revision_id = cursor.lastrowid
    
    logger.info(f"Revision created: id={revision_id}, product={product_name}, discount={discount_percent}%")
    
    # Логируем действие
    log_revision_action(
        revision_id=revision_id,
        user_id=session['user_id'],
        full_name=session['full_name'],
        action='create',
        new_value={
            'product_name': product_name,
            'retail_price': retail_price,
            'expiry_date': expiry_date,
            'barcode': barcode,
            'discount_percent': discount_percent,
            'final_price': final_price
        }
    )
    
    # Если срок истёк — отправляем уведомление админу
    if days_remaining < 0:
        send_expired_notification(revision_id, cursor)
        db.commit()
    
    db.close()
    
    return jsonify({
        'status': 'success',
        'message': 'Товар добавлен на ревизию',
        'revision_id': revision_id,
        'discount_percent': discount_percent,
        'final_price': final_price
    })


@revision_bp.route('/revisions/<int:revision_id>', methods=['PUT'])
def update_revision(revision_id):
    """Выполнить операцию с товаром (19 типов)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    action = data.get('status')  # Тип операции
    
    # Получаем количество: если передано 0, то оставляем 0, иначе по умолчанию 1
    quantity_value = data.get('quantity')
    if quantity_value is not None:
        try:
            quantity = int(quantity_value)
        except (ValueError, TypeError):
            quantity = 1
    else:
        quantity = 1
        
    sale_price = float(data.get('sale_price', 0)) if data.get('sale_price') else None
    reason = data.get('reason', '')
    notes = data.get('notes', '')

    # Допустимые типы операций
    valid_actions = [
        'sold', 'sold_discount', 'sold_promo',  # Продажи
        'written_off_expired', 'written_off_damaged', 'written_off_lost',  # Списание
        'taken_personal', 'taken_gift', 'taken_test',  # Личное
        'returned_supplier', 'exchanged_supplier', 'exchanged_customer', 'returned_customer',  # Обмен/Возврат
        'transferred_store', 'transferred_branch',  # Перемещение
        'utilized', 'donated',  # Утилизация/Пожертвование
        'price_increased', 'price_decreased'  # Изменение цены
    ]

    if action not in valid_actions:
        return jsonify({'status': 'error', 'message': 'Некорректный тип операции'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем товар
    cursor.execute('SELECT * FROM product_revisions WHERE id = ?', (revision_id,))
    rev = cursor.fetchone()

    if not rev:
        return jsonify({'status': 'error', 'message': 'Товар не найден'}), 404

    # Определяем уменьшает ли операция количество
    reduces_quantity = action not in ['price_increased', 'price_decreased', 'returned_customer']

    quantity_before = rev['quantity']
    
    # Для операций, которые не уменьшают количество, quantity_after = quantity_before
    if reduces_quantity:
        quantity_after = quantity_before - quantity
    else:
        quantity_after = quantity_before

    # Проверяем количество для операций, которые уменьшают количество
    if reduces_quantity and quantity > 0 and rev['quantity'] < quantity:
        return jsonify({'status': 'error', 'message': f'Недостаточно товара. Осталось: {rev["quantity"]} шт'}), 400

    # Записываем в журнал операций
    cursor.execute('''
        INSERT INTO revision_transactions
        (revision_id, user_id, full_name, action, quantity, price, quantity_before, quantity_after, reason, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        revision_id,
        session['user_id'],
        session['full_name'],
        action,
        quantity if reduces_quantity else 0,
        sale_price if sale_price else rev['final_price'],
        quantity_before,
        quantity_after,
        reason,
        notes
    ))

    # Обновляем товар
    if reduces_quantity:
        if quantity_after > 0:
            # Ещё есть товар — обновляем только количество
            cursor.execute('''
                UPDATE product_revisions
                SET quantity = ?, updated_at = ?
                WHERE id = ?
            ''', (quantity_after, datetime.now(), revision_id))
        else:
            # Всё списано — меняем статус
            cursor.execute('''
                UPDATE product_revisions
                SET quantity = 0, status = ?, updated_at = ?
                WHERE id = ?
            ''', (action, datetime.now(), revision_id))
    else:
        # Операция не влияет на количество (изменение цены)
        cursor.execute('''
            UPDATE product_revisions
            SET updated_at = ?
            WHERE id = ?
        ''', (datetime.now(), revision_id))

    db.commit()
    db.close()

    logger.info(f"Revision {revision_id} {action}: quantity={quantity}, user={session['user_id']}")

    return jsonify({
        'status': 'success',
        'message': f'Операция выполнена: {action}',
        'quantity_before': quantity_before,
        'quantity_after': quantity_after
    })


@revision_bp.route('/revisions/<int:revision_id>', methods=['DELETE'])
def delete_revision(revision_id):
    """Удалить товар (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Проверяем существует ли
    cursor.execute('SELECT * FROM product_revisions WHERE id = ?', (revision_id,))
    rev = cursor.fetchone()
    
    if not rev:
        db.close()
        return jsonify({'status': 'error', 'message': 'Товар не найден'}), 404
    
    # Удаляем
    cursor.execute('DELETE FROM product_revisions WHERE id = ?', (revision_id,))
    db.commit()
    
    # Логируем
    log_revision_action(
        revision_id=revision_id,
        user_id=session['user_id'],
        full_name=session['full_name'],
        action='delete',
        old_value={
            'product_name': rev['product_name'],
            'retail_price': rev['retail_price'],
            'expiry_date': rev['expiry_date']
        }
    )
    
    db.close()
    
    logger.info(f"Revision {revision_id} deleted by admin")
    
    return jsonify({'status': 'success', 'message': 'Товар удалён'})


@revision_bp.route('/revisions/<int:revision_id>', methods=['PATCH'])
def edit_revision(revision_id):
    """Редактировать товар (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    data = request.json or {}
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Проверяем существует ли
    cursor.execute('SELECT * FROM product_revisions WHERE id = ?', (revision_id,))
    rev = cursor.fetchone()
    
    if not rev:
        db.close()
        return jsonify({'status': 'error', 'message': 'Товар не найден'}), 404
    
    # Собираем старые значения
    old_values = {
        'product_name': rev['product_name'],
        'retail_price': rev['retail_price'],
        'expiry_date': rev['expiry_date'],
        'barcode': rev['barcode'],
        'quantity': rev['quantity']
    }
    
    # Обновляем поля
    updates = []
    params = []
    
    if 'product_name' in data:
        updates.append('product_name = ?')
        params.append(data['product_name'].strip())
    
    if 'quantity' in data:
        updates.append('quantity = ?')
        params.append(int(data['quantity']))
    
    if 'barcode' in data:
        updates.append('barcode = ?')
        params.append(data['barcode'].strip())
    
    if 'retail_price' in data:
        updates.append('retail_price = ?')
        params.append(float(data['retail_price']))
    
    if 'expiry_date' in data:
        # Пересчитываем скидку при изменении срока
        days_remaining, discount_percent, status = calculate_discount(data['expiry_date'])
        final_price = float(data['retail_price']) * (1 - discount_percent / 100) if 'retail_price' in data else rev['final_price']
        
        updates.append('expiry_date = ?')
        params.append(data['expiry_date'])
        updates.append('days_remaining = ?')
        params.append(days_remaining)
        updates.append('discount_percent = ?')
        params.append(discount_percent)
        updates.append('final_price = ?')
        params.append(final_price)
        
        # Обновляем статус если срок истёк
        if days_remaining < 0:
            updates.append('status = ?')
            params.append('admin_decision')
    
    if not updates:
        db.close()
        return jsonify({'status': 'error', 'message': 'Нет данных для обновления'}), 400
    
    params.append(revision_id)
    
    cursor.execute(f'''
        UPDATE product_revisions
        SET {', '.join(updates)}
        WHERE id = ?
    ''', params)
    
    db.commit()
    
    # Собираем новые значения
    new_values = {**old_values, **data}
    
    # Логируем
    log_revision_action(
        revision_id=revision_id,
        user_id=session['user_id'],
        full_name=session['full_name'],
        action='edit',
        old_value=old_values,
        new_value=new_values
    )
    
    db.close()
    
    logger.info(f"Revision {revision_id} edited by admin")
    
    return jsonify({'status': 'success', 'message': 'Товар обновлён'})


@revision_bp.route('/revisions/<int:revision_id>/decision', methods=['POST'])
def admin_decision(revision_id):
    """
    Решение администратора по просроченному товару
    decision: 'reserve' (забрать себе) или 'sell' (разрешить продать)
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    data = request.json or {}
    decision = data.get('decision')
    
    if decision not in ['reserve', 'sell']:
        return jsonify({'status': 'error', 'message': 'Некорректное решение'}), 400
    
    db = get_db_connection()
    cursor = db.cursor()
    
    if decision == 'reserve':
        new_status = 'reserved_admin'
        message = 'Товар забронирован администратором'
    else:  # sell
        new_status = 'active'
        message = 'Разрешено к продаже со скидкой 50%'
    
    cursor.execute('''
        UPDATE product_revisions
        SET status = ?, admin_decision = ?, admin_decision_at = ?, admin_vk_id = ?
        WHERE id = ?
    ''', (
        new_status,
        decision,
        datetime.now(),
        session['user_id'],
        revision_id
    ))

    db.commit()
    
    # Логируем действие
    log_revision_action(
        revision_id=revision_id,
        user_id=session['user_id'],
        full_name=session['full_name'],
        action='admin_decision',
        old_value={'status': 'admin_decision'},
        new_value={'status': new_status, 'decision': decision}
    )
    
    db.close()

    logger.info(f"Admin decision for revision {revision_id}: {decision}")

    return jsonify({'status': 'success', 'message': message})


@revision_bp.route('/stats', methods=['GET'])
def get_revision_stats():
    """Статистика по ревизии"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()

    # Общая статистика
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN days_remaining < 0 THEN 1 ELSE 0 END) as expired,
            SUM(CASE WHEN status = 'admin_decision' THEN 1 ELSE 0 END) as need_decision,
            SUM(retail_price) as total_value,
            SUM(final_price) as total_final_value
        FROM product_revisions
        WHERE status IN ('active', 'admin_decision')
    ''')

    stats = dict(cursor.fetchone())

    # По категориям скидок
    cursor.execute('''
        SELECT discount_percent, COUNT(*) as count, SUM(final_price) as sum
        FROM product_revisions
        WHERE status = 'active' AND days_remaining >= 0
        GROUP BY discount_percent
    ''')

    by_discount = [dict(row) for row in cursor.fetchall()]

    db.close()

    return jsonify({
        'status': 'success',
        'stats': stats,
        'by_discount': by_discount
    })


@revision_bp.route('/revisions/<int:revision_id>/audit', methods=['GET'])
def get_revision_audit(revision_id):
    """История изменений товара (лог аудита)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('''
        SELECT * FROM revision_audit_log
        WHERE revision_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (revision_id,))

    logs = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({'status': 'success', 'logs': logs})


@revision_bp.route('/audit', methods=['GET'])
def get_all_audit():
    """Все логи аудита (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('''
        SELECT a.*, p.product_name
        FROM revision_audit_log a
        LEFT JOIN product_revisions p ON a.revision_id = p.id
        ORDER BY a.created_at DESC
        LIMIT 100
    ''')

    logs = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({'status': 'success', 'logs': logs})


@revision_bp.route('/revisions/<int:revision_id>/transactions', methods=['GET'])
def get_revision_transactions(revision_id):
    """Журнал операций с конкретным товаром"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute('''
        SELECT t.*, u.full_name as operator_name
        FROM revision_transactions t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE t.revision_id = ?
        ORDER BY t.created_at DESC
    ''', (revision_id,))

    transactions = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({'status': 'success', 'transactions': transactions})


@revision_bp.route('/transactions/my', methods=['GET'])
def get_my_transactions():
    """Мои операции (для сотрудника)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    user_id = session['user_id']
    role = session.get('role', 'employee')

    db = get_db_connection()
    cursor = db.cursor()

    if role == 'admin':
        # Админ видит все операции
        cursor.execute('''
            SELECT t.*, p.product_name, u.full_name as operator_name
            FROM revision_transactions t
            LEFT JOIN product_revisions p ON t.revision_id = p.id
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
            LIMIT 100
        ''')
    else:
        # Сотрудник видит только свои
        cursor.execute('''
            SELECT t.*, p.product_name
            FROM revision_transactions t
            LEFT JOIN product_revisions p ON t.revision_id = p.id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
            LIMIT 100
        ''', (user_id,))

    transactions = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({'status': 'success', 'transactions': transactions})


@revision_bp.route('/stats/employees', methods=['GET'])
def get_employee_stats():
    """Статистика по сотрудникам (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403

    db = get_db_connection()
    cursor = db.cursor()

    # Статистика по каждому сотруднику
    cursor.execute('''
        SELECT 
            t.user_id,
            u.full_name,
            COUNT(*) as total_operations,
            SUM(CASE WHEN t.action = 'sold' THEN t.quantity ELSE 0 END) as total_sold,
            SUM(CASE WHEN t.action = 'sold' THEN t.price * t.quantity ELSE 0 END) as total_revenue,
            SUM(CASE WHEN t.action = 'utilized' THEN t.quantity ELSE 0 END) as total_written_off,
            MAX(t.created_at) as last_operation
        FROM revision_transactions t
        LEFT JOIN users u ON t.user_id = u.id
        GROUP BY t.user_id, u.full_name
        ORDER BY total_sold DESC
    ''')

    employees = [dict(row) for row in cursor.fetchall()]

    # Общая статистика
    cursor.execute('''
        SELECT 
            COUNT(*) as total_operations,
            SUM(CASE WHEN action = 'sold' THEN quantity ELSE 0 END) as total_sold,
            SUM(CASE WHEN action = 'sold' THEN price * quantity ELSE 0 END) as total_revenue,
            SUM(CASE WHEN action = 'utilized' THEN quantity ELSE 0 END) as total_written_off
        FROM revision_transactions
    ''')

    total = dict(cursor.fetchone())
    db.close()

    return jsonify({
        'status': 'success',
        'employees': employees,
        'total': total
    })


def send_expired_notification(revision_id, cursor=None):
    """Отправить уведомление админу о просроченном товаре + создать напоминание"""
    close_db = False
    if cursor is None:
        db = get_db_connection()
        cursor = db.cursor()
        close_db = True
    
    cursor.execute('''
        SELECT r.*, u.vk_id
        FROM product_revisions r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
    ''', (revision_id,))
    
    rev = cursor.fetchone()
    if not rev:
        if close_db:
            db.close()
        return
    
    # Обновляем флаг уведомления
    cursor.execute('UPDATE product_revisions SET notification_sent = 1 WHERE id = ?', (revision_id,))
    
    # Создаём напоминание для сотрудников
    try:
        from web_reminders import create_revision_reminder
        create_revision_reminder(
            product_name=rev['product_name'],
            expiry_date=rev['expiry_date'],
            cursor=cursor
        )
    except Exception as e:
        logger.error(f"Failed to create revision reminder: {e}")
    
    if close_db:
        db.commit()
        db.close()
    
    # Формируем сообщение
    msg = (
        f"⚠️ *Внимание! Товар просрочен*\n\n"
        f"📦 *Товар:* {rev['product_name']}\n"
        f"💰 *Розничная цена:* {rev['retail_price']:.2f} ₽\n"
        f"🏷️ *Цена со скидкой 50%:* {rev['final_price']:.2f} ₽\n"
        f"👤 *Сотрудник:* {rev['full_name']}\n\n"
        f"Примите решение:"
    )
    
    # Отправляем в VK чат
    config = vk_bot.get_config()
    admin_vk_id = config.get('admin_vk_id')
    chat_peer_id = config.get('chat_peer_id')
    
    if admin_vk_id:
        # Личное сообщение админу
        vk_bot.send_message(
            peer_id=admin_vk_id,
            message=msg + "\n\nОткройте вкладку «Ревизия» для принятия решения."
        )
    
    if chat_peer_id:
        # Сообщение в общий чат
        vk_bot.send_message(
            peer_id=chat_peer_id,
            message=msg
        )
    
    logger.info(f"Expired notification sent for revision {revision_id}")


def check_daily_expirations():
    """
    Ежедневная проверка — вызвать из планировщика
    Обновляет скидки и статусы для всех товаров
    """
    db = get_db_connection()
    cursor = db.cursor()
    
    today = datetime.now().date()
    
    # Получаем все активные товары
    cursor.execute('''
        SELECT id, expiry_date, retail_price, status, days_remaining, discount_percent, final_price
        FROM product_revisions
        WHERE status IN ('active', 'admin_decision')
    ''')
    
    products = cursor.fetchall()
    updated_count = 0
    expired_count = 0
    
    for rev in products:
        # Пересчитываем скидку
        days_remaining, discount_percent, status = calculate_discount(rev['expiry_date'])
        final_price = rev['retail_price'] * (1 - discount_percent / 100)
        
        # Определяем новый статус
        if days_remaining < 0:
            new_status = 'admin_decision'  # Требует решения админа
            expired_count += 1
        else:
            new_status = 'active'
        
        # Обновляем если изменилось
        if (rev['days_remaining'] != days_remaining or 
            rev['discount_percent'] != discount_percent or 
            rev['status'] != new_status):
            
            cursor.execute('''
                UPDATE product_revisions
                SET days_remaining = ?, discount_percent = ?, final_price = ?, status = ?
                WHERE id = ?
            ''', (days_remaining, discount_percent, final_price, new_status, rev['id']))
            
            updated_count += 1
            
            # Если товар только что просрочился — отправляем уведомление
            if days_remaining < 0 and rev['days_remaining'] >= 0:
                logger.info(f"Product just expired: {rev['id']}, sending notification")
                # Уведомление отправим отдельно
    
    db.commit()
    
    # Товары у которых срок истекает сегодня (для напоминания)
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE date(expiry_date) = ?
        AND status = 'active'
    ''', (today.isoformat(),))
    
    expiring_today = cursor.fetchall()
    
    db.close()
    
    logger.info(f"Daily check: {updated_count} products updated, {expired_count} expired, {len(expiring_today)} expiring today")
    
    return {
        'updated': updated_count,
        'expired': expired_count,
        'expiring_today': len(expiring_today)
    }


def send_weekly_report():
    """
    Еженедельный отчёт — вызвать из планировщика раз в неделю
    """
    db = get_db_connection()
    cursor = db.cursor()
    
    # Товары требующие решения
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE status = 'admin_decision'
        ORDER BY expiry_date DESC
    ''')
    
    need_decision = cursor.fetchall()
    
    # Товары с большой скидкой
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE discount_percent >= 40 AND status = 'active'
        ORDER BY days_remaining ASC
        LIMIT 10
    ''')
    
    high_discount = cursor.fetchall()
    
    db.close()
    
    if not need_decision and not high_discount:
        return 0
    
    # Формируем отчёт
    msg = "📊 *Отчёт по ревизии товаров*\n\n"
    
    if need_decision:
        msg += f"🔴 *Требуют решения админа:* {len(need_decision)}\n"
        for rev in need_decision[:5]:
            msg += f"• {rev['product_name']} — {rev['full_name']}\n"
        if len(need_decision) > 5:
            msg += f"... и ещё {len(need_decision) - 5}\n"
        msg += "\n"
    
    if high_discount:
        msg += f"🟠 *Большая скидка (40%+):* {len(high_discount)}\n"
        for rev in high_discount[:5]:
            msg += f"• {rev['product_name']} — скидка {rev['discount_percent']}%\n"
    
    # Отправляем в чат
    config = vk_bot.get_config()
    chat_peer_id = config.get('chat_peer_id')
    
    if chat_peer_id:
        vk_bot.send_message(peer_id=chat_peer_id, message=msg)
    
    logger.info(f"Weekly revision report sent: {len(need_decision)} need decision, {len(high_discount)} high discount")

    return len(need_decision) + len(high_discount)


# ============================================================================
# УМНАЯ СИСТЕМА КОНТРОЛЯ ТОВАРОВ (v2.0)
# ============================================================================

def get_on_shift_warnings():
    """
    ЭТАП 1: Предупреждения для сотрудника при запуске смены
    Возвращает товары которые требуют внимания:
    - Истекают ≤7 дней (критично)
    - Истекают ≤30 дней (внимание)
    - Без операций >14 дней (застой)
    """
    db = get_db_connection()
    cursor = db.cursor()

    warnings = {
        'critical': [],    # ≤7 дней
        'warning': [],     # ≤30 дней
        'stagnant': [],    # без операций >14 дней
        'total_value': 0
    }

    # Критичные: истекают ≤7 дней
    cursor.execute('''
        SELECT id, product_name, barcode, quantity, retail_price, final_price,
               discount_percent, days_remaining, expiry_date, full_name,
               datetime(created_at, 'localtime') as created_at
        FROM product_revisions
        WHERE status IN ('active', 'admin_decision')
        AND days_remaining BETWEEN 0 AND 7
        ORDER BY days_remaining ASC
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        rev['days_text'] = format_days_remaining(rev['days_remaining'])
        rev['priority'] = 'critical'
        warnings['critical'].append(rev)
        warnings['total_value'] += rev['final_price'] or 0

    # Предупреждения: истекают ≤30 дней
    cursor.execute('''
        SELECT id, product_name, barcode, quantity, retail_price, final_price,
               discount_percent, days_remaining, expiry_date, full_name,
               datetime(created_at, 'localtime') as created_at
        FROM product_revisions
        WHERE status = 'active'
        AND days_remaining BETWEEN 8 AND 30
        ORDER BY days_remaining ASC
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        rev['days_text'] = format_days_remaining(rev['days_remaining'])
        rev['priority'] = 'warning'
        warnings['warning'].append(rev)
        warnings['total_value'] += rev['final_price'] or 0

    # Застойные: без операций >14 дней
    cursor.execute('''
        SELECT pr.id, pr.product_name, pr.barcode, pr.quantity, pr.retail_price,
               pr.final_price, pr.discount_percent, pr.days_remaining, pr.expiry_date,
               pr.full_name, pr.created_at,
               MAX(rt.created_at) as last_operation
        FROM product_revisions pr
        LEFT JOIN revision_transactions rt ON pr.id = rt.revision_id
        WHERE pr.status = 'active'
        AND pr.days_remaining > 30
        GROUP BY pr.id
        HAVING last_operation IS NULL OR julianday('now') - julianday(last_operation) > 14
        ORDER BY last_operation ASC
        LIMIT 10
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        rev['priority'] = 'stagnant'
        warnings['stagnant'].append(rev)

    db.close()

    return warnings


def get_smart_recommendations():
    """
    ЭТАП 2: Умные рекомендации по приоритету
    Возвращает приоритезированный список что проверить
    """
    db = get_db_connection()
    cursor = db.cursor()

    recommendations = []

    # 1. Просроченные без решения админа (КРИТИЧНО)
    cursor.execute('''
        SELECT id, product_name, barcode, quantity, retail_price, final_price,
               discount_percent, days_remaining, expiry_date, full_name,
               datetime(created_at, 'localtime') as created_at
        FROM product_revisions
        WHERE status = 'admin_decision'
        ORDER BY expiry_date ASC
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        recommendations.append({
            'type': 'expired_no_decision',
            'priority': 'critical',
            'icon': '🔴',
            'title': 'Просрочен без решения',
            'description': f'{rev["product_name"]} — просрочен {abs(rev["days_remaining"])} дн.',
            'action': 'admin_decision',
            'revision_id': rev['id'],
            'data': rev
        })

    # 2. Истекают ≤7 дней (ВЫСОКИЙ)
    cursor.execute('''
        SELECT id, product_name, barcode, quantity, retail_price, final_price,
               discount_percent, days_remaining, expiry_date, full_name,
               datetime(created_at, 'localtime') as created_at
        FROM product_revisions
        WHERE status = 'active'
        AND days_remaining BETWEEN 0 AND 7
        ORDER BY days_remaining ASC
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        recommendations.append({
            'type': 'expiring_soon',
            'priority': 'high',
            'icon': '🟠',
            'title': 'Истекает скоро',
            'description': f'{rev["product_name"]} — {rev["days_remaining"]} дн. (скидка {rev["discount_percent"]}%)',
            'action': 'check_and_sell',
            'revision_id': rev['id'],
            'data': rev
        })

    # 3. Истекают ≤30 дней (СРЕДНИЙ)
    cursor.execute('''
        SELECT id, product_name, barcode, quantity, retail_price, final_price,
               discount_percent, days_remaining, expiry_date, full_name,
               datetime(created_at, 'localtime') as created_at
        FROM product_revisions
        WHERE status = 'active'
        AND days_remaining BETWEEN 8 AND 30
        ORDER BY days_remaining ASC
        LIMIT 20
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        recommendations.append({
            'type': 'expiring_medium',
            'priority': 'medium',
            'icon': '🟡',
            'title': 'Истекает через месяц',
            'description': f'{rev["product_name"]} — {rev["days_remaining"]} дн. (скидка {rev["discount_percent"]}%)',
            'action': 'monitor',
            'revision_id': rev['id'],
            'data': rev
        })

    # 4. Застойные товары (>14 дней без операций)
    cursor.execute('''
        SELECT pr.id, pr.product_name, pr.barcode, pr.quantity, pr.retail_price,
               pr.final_price, pr.discount_percent, pr.days_remaining, pr.expiry_date,
               pr.full_name, pr.created_at,
               MAX(rt.created_at) as last_operation
        FROM product_revisions pr
        LEFT JOIN revision_transactions rt ON pr.id = rt.revision_id
        WHERE pr.status = 'active'
        AND pr.days_remaining > 30
        GROUP BY pr.id
        HAVING last_operation IS NULL OR julianday('now') - julianday(last_operation) > 14
        ORDER BY last_operation ASC
        LIMIT 10
    ''')

    for row in cursor.fetchall():
        rev = dict(row)
        days_since = int((datetime.now().date() - datetime.strptime(rev['last_operation'][:10], '%Y-%m-%d').date()).days) if rev['last_operation'] else 999
        recommendations.append({
            'type': 'stagnant',
            'priority': 'low',
            'icon': '🔵',
            'title': 'Без движений',
            'description': f'{rev["product_name"]} — {days_since} дн. без операций',
            'action': 'check_status',
            'revision_id': rev['id'],
            'data': rev
        })

    db.close()

    return recommendations


def send_pre_expiry_alerts():
    """
    ЭТАП 3: Заблаговременные уведомления ДО просрочки
    - За 14 дней: уведомление сотруднику
    - За 7 дней: VK чат
    - За 3 дня: экстренное админу
    - За 1 день: КРИТИЧЕСКОЕ
    """
    db = get_db_connection()
    cursor = db.cursor()

    alerts_sent = {'14_days': 0, '7_days': 0, '3_days': 0, '1_day': 0}

    # За 14 дней
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE status = 'active'
        AND days_remaining = 14
        AND notification_sent = 0
    ''')

    for rev in cursor.fetchall():
        # Отправляем уведомление сотруднику
        logger.info(f"14-day alert: {rev['product_name']} by {rev['full_name']}")
        alerts_sent['14_days'] += 1
        # TODO: Отправить push/email сотруднику

    # За 7 дней
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE status = 'active'
        AND days_remaining = 7
        AND (notification_sent = 0 OR notification_sent = 1)
    ''')

    products_7days = cursor.fetchall()
    if products_7days:
        msg = f"⚠️ *ВНИМАНИЕ: {len(products_7days)} товаров истекает через 7 дней*\n\n"
        for rev in products_7days[:10]:
            msg += f"• {rev['product_name']} — скидка {rev['discount_percent']}%\n"
        msg += "\nПроверьте товары и предложите покупателям!"

        config = vk_bot.get_config()
        chat_peer_id = config.get('chat_peer_id')
        if chat_peer_id:
            vk_bot.send_message(peer_id=chat_peer_id, message=msg)

        alerts_sent['7_days'] = len(products_7days)

    # За 3 дня
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE status = 'active'
        AND days_remaining = 3
        AND notification_sent <= 1
    ''')

    products_3days = cursor.fetchall()
    if products_3days:
        msg = f"🔴 *ЭКСТРЕННО: {len(products_3days)} товаров истекает через 3 дня!*\n\n"
        for rev in products_3days[:10]:
            msg += f"• {rev['product_name']} — {rev['full_name']}\n"
        msg += "\nНеобходимо срочно продать или списать!"

        config = vk_bot.get_config()
        admin_vk_id = config.get('admin_vk_id')
        chat_peer_id = config.get('chat_peer_id')

        # Админу в личку
        if admin_vk_id:
            vk_bot.send_message(user_id=admin_vk_id, message=msg)
        # И в чат
        if chat_peer_id:
            vk_bot.send_message(peer_id=chat_peer_id, message=msg)

        alerts_sent['3_days'] = len(products_3days)

    # За 1 день
    cursor.execute('''
        SELECT * FROM product_revisions
        WHERE status = 'active'
        AND days_remaining = 1
        AND notification_sent <= 1
    ''')

    products_1day = cursor.fetchall()
    if products_1day:
        msg = f"🚨 *КРИТИЧЕСКИ: {len(products_1day)} товаров истекает ЗАВТРА!*\n\n"
        for rev in products_1day:
            msg += f"🔴 {rev['product_name']} — {rev['full_name']}\n"
        msg += "\nПРОДАТЬ ИЛИ СПИСАТЬ СЕГОДНЯ!"

        config = vk_bot.get_config()
        admin_vk_id = config.get('admin_vk_id')
        chat_peer_id = config.get('chat_peer_id')

        # Админу в личку
        if admin_vk_id:
            vk_bot.send_message(user_id=admin_vk_id, message=msg)
        # И в чат
        if chat_peer_id:
            vk_bot.send_message(peer_id=chat_peer_id, message=msg)

        alerts_sent['1_day'] = len(products_1day)

    db.close()

    total = sum(alerts_sent.values())
    if total > 0:
        logger.info(f"Pre-expiry alerts sent: {alerts_sent}")

    return alerts_sent


# ============================================================================
# API ENDPOINTS ДЛЯ УМНОЙ СИСТЕМЫ
# ============================================================================

@revision_bp.route('/warnings', methods=['GET'])
def api_get_warnings():
    """ЭТАП 1: Получить предупреждения для запуска смены"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    days = request.args.get('days', type=int, default=7)

    warnings = get_on_shift_warnings()

    return jsonify({
        'status': 'success',
        'warnings': warnings,
        'total_critical': len(warnings['critical']),
        'total_warning': len(warnings['warning']),
        'total_stagnant': len(warnings['stagnant']),
        'total_value': warnings['total_value']
    })


@revision_bp.route('/recommendations', methods=['GET'])
def api_get_recommendations():
    """ЭТАП 2: Получить умные рекомендации"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    recommendations = get_smart_recommendations()

    return jsonify({
        'status': 'success',
        'recommendations': recommendations,
        'total': len(recommendations),
        'critical': len([r for r in recommendations if r['priority'] == 'critical']),
        'high': len([r for r in recommendations if r['priority'] == 'high']),
        'medium': len([r for r in recommendations if r['priority'] == 'medium']),
        'low': len([r for r in recommendations if r['priority'] == 'low'])
    })


@revision_bp.route('/pre-expiry-alerts', methods=['POST'])
def api_send_pre_expiry_alerts():
    """ЭТАП 3: Отправить заблаговременные уведомления (админ)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403

    alerts = send_pre_expiry_alerts()

    return jsonify({
        'status': 'success',
        'message': 'Уведомления отправлены',
        'alerts': alerts
    })
