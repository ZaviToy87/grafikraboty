# -*- coding: utf-8 -*-
"""
web_work_journal.py — Рабочий журнал API

Функции:
- Открытие/закрытие смен
- Запись в журнал
- Просмотр истории
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from web_config import logger, get_db_connection

wj_bp = Blueprint('work_journal', __name__)


@wj_bp.route('', methods=['GET'])
def get_work_journal():
    """Получить смены рабочего журнала"""
    logger.debug(f"=== WORK JOURNAL: GET / ===")
    logger.debug(f"  Session: user_id={session.get('user_id')}, role={session.get('role')}")
    logger.debug(f"  Request args: {request.args.to_dict()}")
    
    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    user_id = request.args.get('user_id', type=int)
    
    # Для админа показываем все смены, для сотрудника — только его
    if session.get('role') != 'admin':
        user_id = session['user_id']

    db = get_db_connection()
    cursor = db.cursor()

    # Получаем смены с информацией о статусе (открыта/закрыта)
    cursor.execute('''
        SELECT s.id, s.user_id, s.year, s.month, s.day, s.task_ids, s.notes, s.created_at,
               u.full_name,
               (SELECT COUNT(*) FROM work_journal_entries e WHERE e.shift_id = s.id AND e.kind = 'opening') as opening_count,
               (SELECT COUNT(*) FROM work_journal_entries e WHERE e.shift_id = s.id AND e.kind = 'closing') as closing_count,
               (SELECT SUM(e.amount) FROM work_journal_entries e WHERE e.shift_id = s.id AND e.kind = 'opening') as opening_sum,
               (SELECT SUM(e.amount) FROM work_journal_entries e WHERE e.shift_id = s.id AND e.kind = 'closing') as closing_sum
        FROM schedule s
        JOIN users u ON s.user_id = u.id
        WHERE s.year = ? AND s.month = ?
        AND (s.task_ids LIKE '%6%' OR s.task_ids LIKE '%"Смена физическая"%')
        ORDER BY s.day DESC
    ''', (year, month))

    shifts = []
    today = datetime.now().day
    
    for row in cursor.fetchall():
        is_open = row['opening_count'] > 0 and row['closing_count'] == 0
        is_closed = row['closing_count'] > 0
        is_today = row['day'] == today

        # Показываем только: открытые смены + сегодня
        if is_open or is_today:
            shifts.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'full_name': row['full_name'],
                'year': row['year'],
                'month': row['month'],
                'day': row['day'],
                'task_ids': row['task_ids'],
                'notes': row['notes'],
                'created_at': row['created_at'],
                'is_open': is_open,
                'is_closed': is_closed,
                'closing_count': row['closing_count'],
                'opening_sum': row['opening_sum'] or 0,
                'closing_sum': row['closing_sum'] or 0
            })

    logger.debug(f"  Found {len(shifts)} shifts to display")
    
    return jsonify({'status': 'success', 'shifts': shifts})


def find_or_create_shift(cursor, user_id, year, month, day):
    """Найти смену по дате или создать новую"""
    # Ищем смену с "Смена физическая" (task_id=6)
    cursor.execute('''
        SELECT id FROM schedule
        WHERE year = ? AND month = ? AND day = ?
        AND user_id = ?
        AND (task_ids LIKE '%6%' OR task_ids LIKE '%["6"]%')
    ''', (year, month, day, user_id))

    row = cursor.fetchone()
    if not row:
        # Смена не найдена - создаём её автоматически
        cursor.execute('''
            INSERT INTO schedule (user_id, year, month, day, task_ids, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, year, month, day, '["6"]', 'Auto-created for work journal', datetime.now()))
        db = get_db_connection()
        db.commit()
        shift_id = cursor.lastrowid
        logger.info(f"Created shift_id={shift_id}")
        return shift_id
    else:
        logger.info(f"Found shift_id={row[0]}")
        return row[0]


def create_opening_entry(cursor, shift_id, user_id, opening_sum):
    """Создать запись об открытии смены"""
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, 'opening', ?, 'Открытие смены', ?)
    ''', (shift_id, user_id, opening_sum, datetime.now()))


@wj_bp.route('/open', methods=['POST'])
def open_shift():
    """Открыть смену"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    logger.info(f"Work journal open request: data={data}")

    # Пробуем получить shift_id или ищем смену по дате
    shift_id = data.get('shift_id')

    if not shift_id:
        # Ищем смену по дате
        year = int(data.get('year', 0))
        month = int(data.get('month', 0))
        day = int(data.get('day', 0))

        logger.info(f"Looking for shift: year={year}, month={month}, day={day}, user_id={session['user_id']}")

        if not year or not month or not day:
            return jsonify({'status': 'error', 'message': 'Date or shift_id required'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        shift_id = find_or_create_shift(cursor, session['user_id'], year, month, day)
    else:
        db = get_db_connection()
        cursor = db.cursor()

    shift_id = int(shift_id)
    opening_sum = float(data.get('morning_cash', data.get('opening_sum', 0)))

    # Проверяем смену
    cursor.execute('SELECT * FROM schedule WHERE id = ?', (shift_id,))
    shift = cursor.fetchone()

    if not shift:
        return jsonify({'status': 'error', 'message': 'Shift not found'}), 404

    # Создаём запись об открытии
    create_opening_entry(cursor, shift_id, session['user_id'], opening_sum)
    db.commit()

    logger.info(f"Work journal shift opened: shift_id={shift_id}, opening_sum={opening_sum}")

    return jsonify({
        'status': 'success',
        'message': 'Смена открыта',
        'shift_id': shift_id
    })


@wj_bp.route('/entry', methods=['POST'])
def add_entry():
    """Добавить запись в журнал"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}
    shift_id = int(data.get('shift_id', 0))
    amount = float(data.get('amount', 0))
    description = data.get('description', '')
    entry_type = data.get('entry_type', 'sale')

    if not shift_id or not amount:
        return jsonify({'status': 'error', 'message': 'Shift ID and amount required'}), 400
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (shift_id, session['user_id'], entry_type, amount, description, datetime.now()))
    
    db.commit()
    
    logger.info(f"Work journal entry added: shift_id={shift_id}, amount={amount}")
    
    return jsonify({
        'status': 'success',
        'message': 'Запись добавлена'
    })


@wj_bp.route('/entries', methods=['GET'])
def get_entries():
    """Получить записи журнала"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    shift_id = request.args.get('shift_id', type=int)
    
    if not shift_id:
        return jsonify({'status': 'error', 'message': 'Shift ID required'}), 400
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT e.id, e.shift_id, e.user_id, e.kind as entry_type, e.amount, e.note as description, e.created_at,
               u.full_name as user_full_name
        FROM work_journal_entries e
        LEFT JOIN users u ON e.user_id = u.id
        WHERE e.shift_id = ?
        ORDER BY e.created_at
    ''', (shift_id,))
    
    entries = [dict(row) for row in cursor.fetchall()]
    
    # Считаем сумму
    cursor.execute('''
        SELECT
            SUM(CASE WHEN kind = 'sale' THEN amount ELSE 0 END) as total_sales,
            SUM(CASE WHEN kind = 'opening' THEN amount ELSE 0 END) as opening_sum,
            SUM(CASE WHEN kind = 'expense' THEN amount ELSE 0 END) as total_expenses
        FROM work_journal_entries
        WHERE shift_id = ?
    ''', (shift_id,))
    
    totals = cursor.fetchone()
    
    return jsonify({
        'status': 'success',
        'entries': entries,
        'totals': {
            'total_sales': totals['total_sales'] or 0,
            'opening_sum': totals['opening_sum'] or 0,
            'total_expenses': totals['total_expenses'] or 0
        }
    })


@wj_bp.route('/close', methods=['POST'])
def close_shift():
    """Закрыть смену"""
    logger.debug(f"=== WORK JOURNAL: POST /close ===")
    logger.debug(f"  Session: user_id={session.get('user_id')}, role={session.get('role')}")
    
    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    logger.debug(f"  Request data: {data}")
    
    shift_id = int(data.get('shift_id', 0))
    closing_sum = float(data.get('closing_sum', 0))
    notes = data.get('notes', '')

    if not shift_id:
        logger.warning("Shift ID required")
        return jsonify({'status': 'error', 'message': 'Shift ID required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Добавляем запись о закрытии
    logger.debug(f"  Adding closing entry: shift_id={shift_id}, closing_sum={closing_sum}, notes={notes}")
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, 'closing', ?, 'Закрытие смены: ' || ?, ?)
    ''', (shift_id, session['user_id'], closing_sum, notes, datetime.now()))

    # Обновляем смену
    cursor.execute('''
        UPDATE schedule
        SET notes = COALESCE(notes, '') || ' | Закрыта: ' || ?
        WHERE id = ?
    ''', (notes, shift_id))

    db.commit()
    
    logger.info(f"Work journal shift closed: shift_id={shift_id}, closing_sum={closing_sum}")

    return jsonify({
        'status': 'success',
        'message': 'Смена закрыта'
    })


def parse_closing_sum(data):
    """Обработать сумму закрытия из данных"""
    revenue_total = data.get('revenue_total')
    closing_sum = data.get('closing_sum')

    # Если revenue_total есть, используем его как closing_sum
    if revenue_total is not None and revenue_total != '':
        try:
            return float(revenue_total)
        except (ValueError, TypeError):
            return 0.0
    elif closing_sum is not None and closing_sum != '':
        try:
            return float(closing_sum)
        except (ValueError, TypeError):
            return 0.0
    else:
        return 0.0


def parse_closing_notes(data):
    """Обработать заметки закрытия"""
    notes = data.get('notes') or data.get('close_note') or ''
    if notes == 'None' or notes is None:
        notes = ''
    return notes


def create_closing_entry(cursor, shift_id, user_id, closing_sum, notes):
    """Создать запись о закрытии смены"""
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, 'closing', ?, 'Закрытие смены: ' || ?, ?)
    ''', (shift_id, user_id, closing_sum, notes, datetime.now()))


def mark_shift_closed(cursor, shift_id, notes):
    """Пометить смену как закрытую"""
    cursor.execute('''
        UPDATE schedule
        SET notes = COALESCE(notes, '') || ' | Закрыта: ' || ?
        WHERE id = ?
    ''', (notes, shift_id))


@wj_bp.route('/<int:shift_id>/close', methods=['POST'])
def close_shift_by_id(shift_id):
    """Закрыть смену по ID (альтернативный роут)"""
    logger.debug(f"=== WORK JOURNAL: POST /{shift_id}/close ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    logger.debug(f"  Request data: {data}")

    closing_sum = parse_closing_sum(data)
    notes = parse_closing_notes(data)

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем смену
    cursor.execute('SELECT * FROM schedule WHERE id = ?', (shift_id,))
    shift = cursor.fetchone()

    if not shift:
        logger.warning(f"Shift {shift_id} not found")
        return jsonify({'status': 'error', 'message': 'Shift not found'}), 404

    logger.debug(f"  Found shift: user_id={shift['user_id']}, day={shift['day']}")

    # Добавляем запись о закрытии
    logger.debug(f"  Adding closing entry: shift_id={shift_id}, closing_sum={closing_sum}, notes={notes}")
    create_closing_entry(cursor, shift_id, session['user_id'], closing_sum, notes)

    # Обновляем смену - помечаем как закрытую
    mark_shift_closed(cursor, shift_id, notes)
    db.commit()

    logger.info(f"Work journal shift closed: shift_id={shift_id}, closing_sum={closing_sum}")

    return jsonify({
        'status': 'success',
        'message': 'Смена закрыта'
    })


@wj_bp.route('/shift/<int:shift_id>', methods=['GET'])
def get_shift_details(shift_id):
    """Получить детали смены"""
    logger.debug(f"=== WORK JOURNAL: GET /shift/{shift_id} ===")
    
    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()

    # Получаем информацию о смене
    cursor.execute('''
        SELECT s.*, u.full_name
        FROM schedule s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = ?
    ''', (shift_id,))
    
    shift = cursor.fetchone()
    if not shift:
        logger.warning(f"Shift {shift_id} not found")
        return jsonify({'status': 'error', 'message': 'Shift not found'}), 404
    
    shift = dict(shift)

    # Получаем записи журнала
    cursor.execute('''
        SELECT e.id, e.kind, e.amount, e.note, e.created_at, e.user_id,
               u.full_name as user_full_name
        FROM work_journal_entries e
        LEFT JOIN users u ON e.user_id = u.id
        WHERE e.shift_id = ?
        ORDER BY e.created_at
    ''', (shift_id,))

    entries = [dict(row) for row in cursor.fetchall()]

    # Определяем статус
    opening_entry = next((e for e in entries if e['kind'] == 'opening'), None)
    closing_entry = next((e for e in entries if e['kind'] == 'closing'), None)

    # Добавляем entries и другую информацию внутрь shift
    shift['entries'] = entries
    shift['is_open'] = opening_entry is not None and closing_entry is None
    shift['is_closed'] = closing_entry is not None
    shift['opening_sum'] = opening_entry['amount'] if opening_entry else 0
    shift['closing_sum'] = closing_entry['amount'] if closing_entry else 0

    logger.debug(f"  Shift details: is_open={shift['is_open']}, entries={len(entries)}")

    return jsonify({'status': 'success', 'shift': shift})


@wj_bp.route('/shift/<int:shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    """Удалить смену (админ может удалять любые смены)"""
    logger.debug(f"=== WORK JOURNAL: DELETE /shift/{shift_id} ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        logger.warning(f"Non-admin user {session['user_id']} tried to delete shift")
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем есть ли закрытие
    cursor.execute('SELECT id FROM work_journal_entries WHERE shift_id = ? AND kind = ?', (shift_id, 'closing'))
    closing_entry = cursor.fetchone()
    
    if closing_entry:
        # Смена закрыта - удаляем с предупреждением но разрешаем админу
        logger.info(f"Admin deleting closed shift {shift_id}")
        # Сначала удаляем все записи журнала
        cursor.execute('DELETE FROM work_journal_entries WHERE shift_id = ?', (shift_id,))
        logger.info(f"Deleted {cursor.rowcount} journal entries for shift {shift_id}")
    else:
        # Смена открыта - просто удаляем записи
        cursor.execute('DELETE FROM work_journal_entries WHERE shift_id = ?', (shift_id,))

    # Удаляем смену
    cursor.execute('DELETE FROM schedule WHERE id = ?', (shift_id,))
    db.commit()

    logger.info(f"Shift deleted: id={shift_id}")

    return jsonify({'status': 'success', 'message': 'Смена удалена'})


def build_entry_updates(amount, description, entry_type):
    """Построить SQL UPDATE для записи журнала"""
    updates = []
    values = []

    if amount is not None:
        updates.append('amount = ?')
        values.append(float(amount))
    if description:
        updates.append('note = ?')
        values.append(description)
    if entry_type and entry_type in ['sale', 'expense', 'opening', 'closing']:
        updates.append('kind = ?')
        values.append(entry_type)

    return updates, values


@wj_bp.route('/entry/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """Обновить запись в журнале"""
    logger.debug(f"=== WORK JOURNAL: PUT /entry/{entry_id} ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    amount = data.get('amount')
    description = data.get('description')
    entry_type = data.get('entry_type')

    if not amount and not description and not entry_type:
        return jsonify({'status': 'error', 'message': 'Хотя бы одно поле обязательно'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем существование записи
    cursor.execute('SELECT * FROM work_journal_entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()

    if not entry:
        logger.warning(f"Entry {entry_id} not found")
        return jsonify({'status': 'error', 'message': 'Запись не найдена'}), 404

    # Обновляем поля
    updates, values = build_entry_updates(amount, description, entry_type)

    if updates:
        values.append(entry_id)
        cursor.execute(f'''
            UPDATE work_journal_entries SET {', '.join(updates)} WHERE id = ?
        ''', values)
        db.commit()
        logger.info(f"Work journal entry updated: id={entry_id}, updates={updates}")

    return jsonify({'status': 'success', 'message': 'Запись обновлена'})


@wj_bp.route('/entry/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Удалить запись из журнала"""
    logger.debug(f"=== WORK JOURNAL: DELETE /entry/{entry_id} ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    if session.get('role') != 'admin':
        logger.warning(f"Non-admin user {session['user_id']} tried to delete entry")
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем существование записи
    cursor.execute('SELECT * FROM work_journal_entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()

    if not entry:
        logger.warning(f"Entry {entry_id} not found")
        return jsonify({'status': 'error', 'message': 'Запись не найдена'}), 404

    # Нельзя удалять записи об открытии/закрытии если это закроет смену
    if entry['kind'] in ['opening', 'closing']:
        # Проверяем есть ли другие записи
        cursor.execute('SELECT COUNT(*) as count FROM work_journal_entries WHERE shift_id = ?', (entry['shift_id'],))
        if cursor.fetchone()['count'] <= 2:
            logger.warning(f"Cannot delete {entry['kind']} entry - last record for shift {entry['shift_id']}")
            return jsonify({'status': 'error', 'message': 'Нельзя удалить последнюю запись смены'}), 400

    cursor.execute('DELETE FROM work_journal_entries WHERE id = ?', (entry_id,))
    db.commit()

    logger.info(f"Work journal entry deleted: id={entry_id}")

    return jsonify({'status': 'success', 'message': 'Запись удалена'})


@wj_bp.route('/export', methods=['GET'])
def export_work_journal():
    """Экспорт рабочего журнала в CSV"""
    logger.debug(f"=== WORK JOURNAL: GET /export ===")

    if 'user_id' not in session:
        logger.warning("Not authorized")
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not year or not month:
        return jsonify({'status': 'error', 'message': 'Year and month required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Получаем все записи за месяц
    cursor.execute('''
        SELECT e.id, e.shift_id, e.kind, e.amount, e.note, e.created_at,
               s.year, s.month, s.day,
               u.full_name as user_name
        FROM work_journal_entries e
        JOIN schedule s ON e.shift_id = s.id
        JOIN users u ON e.user_id = u.id
        WHERE s.year = ? AND s.month = ?
        ORDER BY s.day, e.created_at
    ''', (year, month))

    entries = cursor.fetchall()

    # Формируем CSV
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Дата', 'Сотрудник', 'Тип', 'Сумма', 'Описание', 'Время создания'])

    for entry in entries:
        writer.writerow([
            f"{entry['day']}.{entry['month']}.{entry['year']}",
            entry['user_name'],
            entry['kind'],
            entry['amount'],
            entry['note'],
            entry['created_at']
        ])

    csv_content = output.getvalue()
    output.close()

    logger.info(f"Work journal exported: {len(entries)} entries for {year}-{month}")

    from flask import make_response
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=work_journal_{year}_{month:02d}.csv'

    return response
