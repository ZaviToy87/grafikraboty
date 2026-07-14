# -*- coding: utf-8 -*-
"""
web_work_journal.py — Рабочий журнал API (обновлённая версия)

Разделение:
- work_schedule — планируемый график (кто ДОЛЖЕН работать)
- work_sessions — фактические смены (кто РЕАЛЬНО работал)
- work_journal_entries — записи журнала (связаны с work_sessions)

Сотрудник САМ открывает/закрывает смену. График не изменяется.
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from web_config import logger, get_db_connection

wj_bp = Blueprint('work_journal', __name__, url_prefix='/api/work-journal')


# ==========================================
# ПОЛУЧЕНИЕ ДАННЫХ
# ==========================================

@wj_bp.route('', methods=['GET'])
def get_work_sessions():
    """Получить список рабочих смен"""
    logger.debug(f"=== WORK SESSIONS: GET / ===")
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    user_id = request.args.get('user_id', type=int)
    
    # Для админа показываем все смены, для сотрудника — только его
    if session.get('role') != 'admin':
        user_id = session['user_id']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Получаем смены из work_sessions
    query = '''
        SELECT 
            ws.id,
            ws.user_id,
            ws.work_schedule_id,
            ws.year,
            ws.month,
            ws.day,
            ws.opened_at,
            ws.closed_at,
            ws.opening_sum,
            ws.closing_sum,
            ws.revenue_total,
            ws.acquiring_amount,
            ws.evening_cash,
            ws.evening_cashless,
            ws.notes,
            ws.status,
            ws.created_at,
            ws.updated_at,
            u.full_name
        FROM work_sessions ws
        JOIN users u ON ws.user_id = u.id
        WHERE ws.year = ? AND ws.month = ?
    '''
    params = [year, month]
    
    if user_id:
        query += ' AND ws.user_id = ?'
        params.append(user_id)
    
    query += ' ORDER BY ws.day DESC'
    
    cursor.execute(query, params)
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'work_schedule_id': row['work_schedule_id'],
            'year': row['year'],
            'month': row['month'],
            'day': row['day'],
            'opened_at': row['opened_at'],
            'closed_at': row['closed_at'],
            'opening_sum': row['opening_sum'] or 0,
            'closing_sum': row['closing_sum'] or 0,
            'revenue_total': row['revenue_total'] or 0,
            'acquiring_amount': row['acquiring_amount'] or 0,
            'evening_cash': row['evening_cash'] or 0,
            'evening_cashless': row['evening_cashless'] or 0,
            'notes': row['notes'],
            'status': row['status'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'full_name': row['full_name'],
            'is_open': row['status'] == 'opened',
            'is_closed': row['status'] == 'closed'
        })
    
    logger.debug(f"  Found {len(sessions)} sessions")
    
    return jsonify({'status': 'success', 'sessions': sessions})


@wj_bp.route('/shift/<int:shift_id>', methods=['GET'])
def get_shift_details(shift_id):
    """Получить детали смены"""
    logger.debug(f"=== WORK SESSIONS: GET /shift/{shift_id} ===")
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Получаем информацию о смене
    cursor.execute('''
        SELECT 
            ws.*,
            u.full_name,
            CASE WHEN ws.status = 'opened' THEN 1 ELSE 0 END as is_open,
            CASE WHEN ws.status = 'closed' THEN 1 ELSE 0 END as is_closed
        FROM work_sessions ws
        JOIN users u ON ws.user_id = u.id
        WHERE ws.id = ?
    ''', (shift_id,))
    
    shift = cursor.fetchone()
    if not shift:
        return jsonify({'status': 'error', 'message': 'Shift not found'}), 404
    
    shift = dict(shift)
    
    # Получаем записи журнала
    cursor.execute('''
        SELECT 
            e.id, e.kind, e.amount, e.note, e.created_at, e.user_id,
            u.full_name as user_full_name
        FROM work_journal_entries e
        LEFT JOIN users u ON e.user_id = u.id
        WHERE e.shift_id = ?
        ORDER BY e.created_at
    ''', (shift_id,))
    
    entries = [dict(row) for row in cursor.fetchall()]
    shift['entries'] = entries
    
    logger.debug(f"  Shift details: status={shift['status']}, entries={len(entries)}")
    
    return jsonify({'status': 'success', 'shift': shift})


# ==========================================
# ОТКРЫТИЕ СМЕНЫ
# ==========================================

@wj_bp.route('/open', methods=['POST'])
def open_shift():
    """Открыть смену"""
    logger.debug(f"=== WORK SESSIONS: POST /open ===")

    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    logger.debug(f"  Request data: {data}")

    year = int(data.get('year', 0))
    month = int(data.get('month', 0))
    day = int(data.get('day', 0))
    opening_sum = float(data.get('morning_cash', data.get('opening_sum', 0)))

    if not year or not month or not day:
        return jsonify({'status': 'error', 'message': 'Date required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем, есть ли уже смена на эту дату
    cursor.execute('''
        SELECT id, status FROM work_sessions
        WHERE user_id = ? AND year = ? AND month = ? AND day = ?
    ''', (session['user_id'], year, month, day))

    existing = cursor.fetchone()

    if existing:
        if existing['status'] == 'opened':
            return jsonify({'status': 'error', 'message': 'Смена уже открыта'}), 400
        elif existing['status'] == 'closed':
            return jsonify({'status': 'error', 'message': 'Смена уже закрыта'}), 400

    # Проверяем, есть ли запись в графике на эту дату
    cursor.execute('''
        SELECT id FROM work_schedule
        WHERE user_id = ? AND year = ? AND month = ? AND day = ?
    ''', (session['user_id'], year, month, day))

    schedule_row = cursor.fetchone()
    work_schedule_id = schedule_row['id'] if schedule_row else None

    # Если нет в графике — всё равно создаём смену (сотрудник мог выйти вне графика)
    # Создаём смену
    cursor.execute('''
        INSERT INTO work_sessions
        (user_id, work_schedule_id, year, month, day, opened_at, opening_sum, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'opened')
    ''', (session['user_id'], work_schedule_id, year, month, day, datetime.now(), opening_sum))

    session_id = cursor.lastrowid

    # Создаём запись об открытии в журнале
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, 'opening', ?, 'Открытие смены', ?)
    ''', (session_id, session['user_id'], opening_sum, datetime.now()))

    db.commit()

    logger.info(f"Shift opened: session_id={session_id}, opening_sum={opening_sum}")

    # Отправляем уведомление в VK
    try:
        import vk_bot
        shift_data = {
            'year': year,
            'month': month,
            'day': day,
            'morning_cash': opening_sum  # Исправлено: morning_cash вместо opening_sum
        }
        vk_bot.send_shift_notification('open', session.get('full_name', session['username']), shift_data)
    except Exception as e:
        logger.warning(f"Failed to send VK shift notification: {e}")

    return jsonify({
        'status': 'success',
        'message': 'Смена открыта',
        'session_id': session_id
    })


# ==========================================
# ДОБАВЛЕНИЕ ЗАПИСИ
# ==========================================

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
    
    # Проверяем, что смена открыта
    cursor.execute('SELECT status FROM work_sessions WHERE id = ?', (shift_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        return jsonify({'status': 'error', 'message': 'Смена не найдена'}), 404
    
    if session_row['status'] != 'opened':
        return jsonify({'status': 'error', 'message': 'Нельзя добавить запись в закрытую смену'}), 400
    
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (shift_id, session['user_id'], entry_type, amount, description, datetime.now()))
    
    db.commit()
    
    logger.info(f"Entry added: shift_id={shift_id}, amount={amount}, type={entry_type}")
    
    return jsonify({
        'status': 'success',
        'message': 'Запись добавлена'
    })


# ==========================================
# ЗАКРЫТИЕ СМЕНЫ
# ==========================================

@wj_bp.route('/close', methods=['POST'])
def close_shift():
    """Закрыть смену"""
    logger.debug(f"=== WORK SESSIONS: POST /close ===")

    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    data = request.json or {}
    logger.debug(f"  Request data: {data}")

    shift_id = int(data.get('shift_id', 0))
    closing_sum = float(data.get('closing_sum', 0))
    notes = data.get('notes', '')

    # Дополнительные поля для итогов
    revenue_total = float(data.get('revenue_total') or 0)
    acquiring_amount = float(data.get('acquiring_amount') or 0)
    terminal_actual = float(data.get('terminal_actual') or 0)
    evening_cash = float(data.get('evening_cash') or 0)
    evening_cashless = float(data.get('evening_cashless') or 0) if data.get('evening_cashless') is not None else 0

    if not shift_id:
        return jsonify({'status': 'error', 'message': 'Shift ID required'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Проверяем смену
    cursor.execute('SELECT * FROM work_sessions WHERE id = ?', (shift_id,))
    session_row = cursor.fetchone()

    if not session_row:
        return jsonify({'status': 'error', 'message': 'Смена не найдена'}), 404

    if session_row['status'] == 'closed':
        return jsonify({'status': 'error', 'message': 'Смена уже закрыта'}), 400

    # Добавляем запись о закрытии
    cursor.execute('''
        INSERT INTO work_journal_entries
        (shift_id, user_id, kind, amount, note, created_at)
        VALUES (?, ?, 'closing', ?, 'Закрытие смены: ' || ?, ?)
    ''', (shift_id, session['user_id'], closing_sum, notes, datetime.now()))

    # Обновляем смену
    cursor.execute('''
        UPDATE work_sessions
        SET
            status = 'closed',
            closed_at = ?,
            closing_sum = ?,
            revenue_total = ?,
            acquiring_amount = ?,
            terminal_actual = ?,
            evening_cash = ?,
            evening_cashless = ?,
            notes = COALESCE(notes, '') || ' | Закрыта: ' || ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (datetime.now(), closing_sum, revenue_total, acquiring_amount,
          terminal_actual, evening_cash, evening_cashless, notes, shift_id))

    db.commit()

    logger.info(f"Shift closed: shift_id={shift_id}, closing_sum={closing_sum}")

    # Отправляем уведомление в VK с полным отчётом
    try:
        import vk_bot
        
        # Считаем расходы за смену — раздельно по типам
        cursor.execute('''
            SELECT kind, COALESCE(SUM(amount), 0) as total FROM work_journal_entries
            WHERE shift_id = ? AND kind IN ('Внесла в кассу', 'Отдала деньги', 'Взяла зарплату', 'Сняла в банк')
            GROUP BY kind
        ''', (shift_id,))
        expense_rows = cursor.fetchall()
        
        # Разделяем на "внесла" (+) и "отдала/взяла/сняла" (-)
        expenses_in = 0  # Внесла в кассу — ПЛЮС
        expenses_out = 0  # Отдала деньги, Взяла зарплату, Сняла в банк — МИНУС
        
        for row in expense_rows:
            amount = round(float(row['total']), 2)
            if row['kind'] == 'Внесла в кассу':
                expenses_in += amount
            else:
                expenses_out += amount
        
        # Баланс операций = Внесла - Отдала/Взяла/Сняла
        expenses_balance = round(expenses_in - expenses_out, 2)
        
        # Считаем расхождение
        morning_cash = round(float(session_row['opening_sum'] or 0), 2)
        
        # Наличные по ККТ = Выручка общая - Безнал - Терминал
        cash_revenue = round(revenue_total - acquiring_amount - terminal_actual, 2)
        
        # Должно быть = Утро + Наличные по ККТ + Баланс операций
        expected_cash = round(morning_cash + cash_revenue + expenses_balance, 2)
        actual_cash = round(float(evening_cash), 2)
        discrepancy = round(actual_cash - expected_cash, 2)
        
        shift_data = {
            'year': session_row['year'],
            'month': session_row['month'],
            'day': session_row['day'],
            'morning_cash': morning_cash,
            'revenue_total': revenue_total,
            'acquiring_amount': acquiring_amount,
            'terminal_actual': terminal_actual,
            'evening_cash': evening_cash,
            'evening_cashless': evening_cashless,
            'expenses_in': expenses_in,
            'expenses_out': expenses_out,
            'expenses_balance': expenses_balance,
            'discrepancy': discrepancy
        }
        vk_bot.send_shift_notification('close', session.get('full_name', session['username']), shift_data)
    except Exception as e:
        logger.warning(f"Failed to send VK shift notification: {e}")

    return jsonify({
        'status': 'success',
        'message': 'Смена закрыта'
    })


# ==========================================
# УДАЛЕНИЕ СМЕНЫ (только админ)
# ==========================================

@wj_bp.route('/shift/<int:shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    """Удалить смену (админ может удалять любые смены)"""
    logger.debug(f"=== WORK SESSIONS: DELETE /shift/{shift_id} ===")
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Проверяем смену
    cursor.execute('SELECT * FROM work_sessions WHERE id = ?', (shift_id,))
    session_row = cursor.fetchone()
    
    if not session_row:
        return jsonify({'status': 'error', 'message': 'Смена не найдена'}), 404
    
    # ⚠️ ВАЖНО: Удаляем только смену, график (work_schedule) НЕ трогаем!
    # Сначала удаляем записи журнала
    cursor.execute('DELETE FROM work_journal_entries WHERE shift_id = ?', (shift_id,))
    logger.info(f"Deleted {cursor.rowcount} journal entries for shift {shift_id}")
    
    # Удаляем смену
    cursor.execute('DELETE FROM work_sessions WHERE id = ?', (shift_id,))
    logger.info(f"Deleted work_session: id={shift_id}")
    
    db.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Смена удалена'
    })


# ==========================================
# ОБНОВЛЕНИЕ ЗАПИСЕЙ ЖУРНАЛА
# ==========================================

@wj_bp.route('/entry/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """Обновить запись в журнале"""
    logger.debug(f"=== WORK SESSIONS: PUT /entry/{entry_id} ===")
    
    if 'user_id' not in session:
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
        return jsonify({'status': 'error', 'message': 'Запись не найдена'}), 404
    
    # Обновляем поля
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
    
    if updates:
        values.append(entry_id)
        cursor.execute(f'''
            UPDATE work_journal_entries SET {', '.join(updates)} WHERE id = ?
        ''', values)
        db.commit()
        logger.info(f"Entry updated: id={entry_id}")
    
    return jsonify({'status': 'success', 'message': 'Запись обновлена'})


@wj_bp.route('/entry/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Удалить запись из журнала"""
    logger.debug(f"=== WORK SESSIONS: DELETE /entry/{entry_id} ===")
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Требуется роль администратора'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Проверяем существование записи
    cursor.execute('SELECT * FROM work_journal_entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        return jsonify({'status': 'error', 'message': 'Запись не найдена'}), 404
    
    # Нельзя удалять записи об открытии/закрытии если это закроет смену
    if entry['kind'] in ['opening', 'closing']:
        cursor.execute('SELECT COUNT(*) as count FROM work_journal_entries WHERE shift_id = ?', (entry['shift_id'],))
        if cursor.fetchone()['count'] <= 2:
            return jsonify({'status': 'error', 'message': 'Нельзя удалить последнюю запись смены'}), 400
    
    cursor.execute('DELETE FROM work_journal_entries WHERE id = ?', (entry_id,))
    db.commit()
    
    logger.info(f"Entry deleted: id={entry_id}")
    
    return jsonify({'status': 'success', 'message': 'Запись удалена'})


# ==========================================
# ЭКСПОРТ
# ==========================================

@wj_bp.route('/export', methods=['GET'])
def export_work_journal():
    """Экспорт рабочего журнала в CSV"""
    logger.debug(f"=== WORK SESSIONS: GET /export ===")
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        return jsonify({'status': 'error', 'message': 'Year and month required'}), 400
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Получаем все записи за месяц
    cursor.execute('''
        SELECT 
            e.id, e.shift_id, e.kind, e.amount, e.note, e.created_at,
            ws.year, ws.month, ws.day,
            u.full_name as user_name
        FROM work_journal_entries e
        JOIN work_sessions ws ON e.shift_id = ws.id
        JOIN users u ON e.user_id = u.id
        WHERE ws.year = ? AND ws.month = ?
        ORDER BY ws.day, e.created_at
    ''', (year, month))
    
    entries = cursor.fetchall()

    # Формируем CSV с UTF-8 BOM для Excel
    import csv
    import io
    
    # Используем BytesIO с UTF-8 BOM
    output = io.BytesIO()
    output.write(b'\xef\xbb\xbf')  # UTF-8 BOM для Excel
    
    # Пишем как текст, затем кодируем
    text_output = io.StringIO()
    writer = csv.writer(text_output, delimiter=';')
    writer.writerow(['Дата', 'Сотрудник', 'Тип', 'Сумма', 'Описание', 'Время создания'])

    for entry in entries:
        writer.writerow([
            f"{entry['day']}.{entry['month']}.{entry['year']}",
            entry['user_name'] or '',
            entry['kind'],
            entry['amount'],
            entry['note'] or '',
            entry['created_at']
        ])
    
    # Кодируем в UTF-8
    csv_content = text_output.getvalue().encode('utf-8')
    output.write(csv_content)
    text_output.close()

    logger.info(f"Work journal exported: {len(entries)} entries for {year}-{month}")

    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=work_journal_{year}_{month:02d}.csv'
    output.close()

    return response


# ==========================================
# АНАЛИТИКА ПРОДАЖ (на основе work_sessions)
# ==========================================

@wj_bp.route('/sales-summary', methods=['GET'])
def get_sales_summary():
    """Получить сводку продаж за период"""
    logger.debug(f"=== SALES: GET /sales-summary ===")

    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    db = get_db_connection()
    cursor = db.cursor()

    # Получаем все закрытые смены за период
    cursor.execute('''
        SELECT 
            day,
            revenue_total,
            acquiring_amount,
            terminal_actual,
            evening_cash,
            evening_cashless,
            opening_sum,
            closing_sum,
            full_name,
            closed_at
        FROM work_sessions
        WHERE year = ? AND month = ? AND status = 'closed'
        ORDER BY day
    ''', (year, month))

    shifts = cursor.fetchall()
    db.close()

    # Считаем итоги
    total_revenue = sum(s['revenue_total'] or 0 for s in shifts)
    total_acquiring = sum(s['acquiring_amount'] or 0 for s in shifts)
    total_terminal = sum(s['terminal_actual'] or 0 for s in shifts)
    total_evening_cash = sum(s['evening_cash'] or 0 for s in shifts)
    total_evening_cashless = sum(s['evening_cashless'] or 0 for s in shifts)
    total_opening = sum(s['opening_sum'] or 0 for s in shifts)
    total_closing = sum(s['closing_sum'] or 0 for s in shifts)

    # По дням
    by_day = {}
    for s in shifts:
        day = s['day']
        if day not in by_day:
            by_day[day] = {
                'revenue': 0,
                'acquiring': 0,
                'terminal': 0,
                'cash': 0,
                'shifts': 0
            }
        by_day[day]['revenue'] += s['revenue_total'] or 0
        by_day[day]['acquiring'] += s['acquiring_amount'] or 0
        by_day[day]['terminal'] += s['terminal_actual'] or 0
        by_day[day]['cash'] += s['evening_cash'] or 0
        by_day[day]['shifts'] += 1

    return jsonify({
        'status': 'success',
        'period': {'year': year, 'month': month},
        'summary': {
            'total_revenue': round(total_revenue, 2),
            'total_acquiring': round(total_acquiring, 2),
            'total_terminal': round(total_terminal, 2),
            'total_evening_cash': round(total_evening_cash, 2),
            'total_evening_cashless': round(total_evening_cashless, 2),
            'total_opening': round(total_opening, 2),
            'total_closing': round(total_closing, 2),
            'shifts_count': len(shifts)
        },
        'by_day': by_day
    })
