# -*- coding: utf-8 -*-
"""
web_sync_1c.py — Веб-интерфейс для просмотра синхронизированных данных из 1С
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from web_config import logger, get_db_connection
from datetime import datetime

sync_1c_bp = Blueprint('sync_1c', __name__, url_prefix='/api/sync-1c')


def get_sync_stats():
    """Получает статистику по синхронизированным данным"""
    db = get_db_connection()
    c = db.cursor()
    
    stats = {}
    tables = [
        ('sync_nomenclature', 'Номенклатура'),
        ('sync_barcodes', 'Штрихкоды'),
        ('sync_sales', 'Продажи (документы)'),
        ('sync_sale_items', 'Продажи (товары)'),
        ('sync_receipts', 'Приемки (документы)'),
        ('sync_receipt_items', 'Приемки (товары)'),
        ('sync_counterparties', 'Контрагенты'),
        ('sync_organizations', 'Организации'),
        ('sync_warehouses', 'Склады'),
    ]
    
    for table, label in tables:
        try:
            c.execute(f'SELECT COUNT(*) FROM {table}')
            count = c.fetchone()[0]
            stats[table] = {'label': label, 'count': count}
        except Exception as e:
            stats[table] = {'label': label, 'count': 0, 'error': str(e)}
    
    # Дата последней синхронизации
    try:
        c.execute('SELECT MAX(created_at) FROM sync_log')
        last_sync = c.fetchone()[0]
        stats['last_sync'] = last_sync
    except:
        stats['last_sync'] = None
    
    db.close()
    return stats


@sync_1c_bp.route('/stats')
def get_stats():
    """API: статистика синхронизации"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    return jsonify(get_sync_stats())


@sync_1c_bp.route('/nomenclature')
def get_nomenclature():
    """API: список номенклатуры с пагинацией и поиском"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    group = request.args.get('group', '', type=str)
    offset = (page - 1) * per_page
    
    db = get_db_connection()
    c = db.cursor()
    
    where_clauses = ['is_deleted = 0']
    params = []
    
    if search:
        where_clauses.append('(name LIKE ? OR article LIKE ? OR code LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if group:
        where_clauses.append('group_name = ?')
        params.append(group)
    
    where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
    
    # Общее количество
    c.execute(f'SELECT COUNT(*) FROM sync_nomenclature WHERE {where_sql}', params)
    total = c.fetchone()[0]
    
    # Данные
    c.execute(
        f'SELECT guid, code, name, full_name, article, group_name, vat_rate, type, nomenclature_type, updated_at '
        f'FROM sync_nomenclature WHERE {where_sql} ORDER BY name LIMIT ? OFFSET ?',
        params + [per_page, offset]
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    # Группы для фильтра
    c.execute('SELECT DISTINCT group_name FROM sync_nomenclature WHERE group_name IS NOT NULL AND group_name != "" ORDER BY group_name')
    groups = [row[0] for row in c.fetchall()]
    
    db.close()
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'groups': groups
    })


@sync_1c_bp.route('/sales')
def get_sales():
    """API: список продаж"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page
    
    db = get_db_connection()
    c = db.cursor()
    
    c.execute('SELECT COUNT(*) FROM sync_sales')
    total = c.fetchone()[0]
    
    c.execute(
        'SELECT guid, date, number, organization_name, warehouse_name, total_sum, currency, '
        'cash_register, taxation, updated_at '
        'FROM sync_sales ORDER BY date DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    db.close()
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@sync_1c_bp.route('/sale-items/<guid>')
def get_sale_items(guid):
    """API: товары в продаже"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    db = get_db_connection()
    c = db.cursor()
    
    c.execute(
        'SELECT line_number, nomenclature_name, nomenclature_code, quantity, price, sum, unit '
        'FROM sync_sale_items WHERE sale_guid = ? ORDER BY line_number',
        (guid,)
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    db.close()
    return jsonify({'items': items})


@sync_1c_bp.route('/receipts')
def get_receipts():
    """API: список приемок"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page
    
    db = get_db_connection()
    c = db.cursor()
    
    c.execute('SELECT COUNT(*) FROM sync_receipts')
    total = c.fetchone()[0]
    
    c.execute(
        'SELECT guid, date, number, operation_type, organization_name, warehouse_name, '
        'total_sum, price_type, updated_at '
        'FROM sync_receipts ORDER BY date DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    db.close()
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@sync_1c_bp.route('/receipt-items/<guid>')
def get_receipt_items(guid):
    """API: товары в приемке"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    db = get_db_connection()
    c = db.cursor()
    
    c.execute(
        'SELECT nomenclature_name, nomenclature_code, quantity, price, sum '
        'FROM sync_receipt_items WHERE receipt_guid = ? ORDER BY id',
        (guid,)
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    db.close()
    return jsonify({'items': items})


@sync_1c_bp.route('/counterparties')
def get_counterparties():
    """API: список контрагентов"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    db = get_db_connection()
    c = db.cursor()
    
    c.execute(
        'SELECT guid, code, name, full_name, inn, kpp, legal_address, actual_address, '
        'phone, email, is_deleted, updated_at '
        'FROM sync_counterparties ORDER BY name'
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    db.close()
    return jsonify({'items': items})


@sync_1c_bp.route('/barcodes')
def get_barcodes():
    """API: список штрихкодов"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    offset = (page - 1) * per_page
    
    db = get_db_connection()
    c = db.cursor()
    
    where_clauses = []
    params = []
    
    if search:
        where_clauses.append('(b.barcode LIKE ? OR n.name LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%'])
    
    where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
    
    c.execute(f'SELECT COUNT(*) FROM sync_barcodes b LEFT JOIN sync_nomenclature n ON b.nomenclature_guid = n.guid WHERE {where_sql}', params)
    total = c.fetchone()[0]
    
    c.execute(
        f'SELECT b.barcode, b.nomenclature_guid, n.name as nomenclature_name, n.code as nomenclature_code '
        f'FROM sync_barcodes b LEFT JOIN sync_nomenclature n ON b.nomenclature_guid = n.guid '
        f'WHERE {where_sql} ORDER BY b.barcode LIMIT ? OFFSET ?',
        params + [per_page, offset]
    )
    items = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    db.close()
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


# ==========================================
# API: Аналитика продаж и приемок по дням
# ==========================================

@sync_1c_bp.route('/daily-stats')
def get_daily_stats():
    """API: агрегированные данные продаж и приемок по дням"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    # Параметры фильтрации
    days = request.args.get('days', 30, type=int)
    days = min(max(days, 7), 365)  # от 7 до 365 дней
    
    db = get_db_connection()
    c = db.cursor()
    
    # Продажи по дням
    c.execute('''
        SELECT 
            date(date) as day,
            COUNT(*) as doc_count,
            COALESCE(SUM(total_sum), 0) as total_sum,
            COUNT(DISTINCT organization_name) as org_count,
            COUNT(DISTINCT warehouse_name) as warehouse_count
        FROM sync_sales
        WHERE date(date) >= date('now', ?)
        GROUP BY day
        ORDER BY day ASC
    ''', (f'-{days} days',))
    
    sales_by_day = {}
    for row in c.fetchall():
        sales_by_day[row[0]] = {
            'doc_count': row[1],
            'total_sum': float(row[2]),
            'org_count': row[3],
            'warehouse_count': row[4]
        }
    
    # Приемки по дням
    c.execute('''
        SELECT 
            date(date) as day,
            COUNT(*) as doc_count,
            COALESCE(SUM(total_sum), 0) as total_sum,
            COUNT(DISTINCT organization_name) as org_count,
            COUNT(DISTINCT warehouse_name) as warehouse_count
        FROM sync_receipts
        WHERE date(date) >= date('now', ?)
        GROUP BY day
        ORDER BY day ASC
    ''', (f'-{days} days',))
    
    receipts_by_day = {}
    for row in c.fetchall():
        receipts_by_day[row[0]] = {
            'doc_count': row[1],
            'total_sum': float(row[2]),
            'org_count': row[3],
            'warehouse_count': row[4]
        }
    
    # Количество проданных товаров по дням
    c.execute('''
        SELECT 
            date(s.date) as day,
            COALESCE(SUM(si.quantity), 0) as items_count,
            COALESCE(SUM(si.sum), 0) as items_sum
        FROM sync_sales s
        LEFT JOIN sync_sale_items si ON s.guid = si.sale_guid
        WHERE date(s.date) >= date('now', ?)
        GROUP BY day
        ORDER BY day ASC
    ''', (f'-{days} days',))
    
    sale_items_by_day = {}
    for row in c.fetchall():
        sale_items_by_day[row[0]] = {
            'items_count': float(row[1]),
            'items_sum': float(row[2])
        }
    
    # Количество принятых товаров по дням
    c.execute('''
        SELECT 
            date(r.date) as day,
            COALESCE(SUM(ri.quantity), 0) as items_count,
            COALESCE(SUM(ri.sum), 0) as items_sum
        FROM sync_receipts r
        LEFT JOIN sync_receipt_items ri ON r.guid = ri.receipt_guid
        WHERE date(r.date) >= date('now', ?)
        GROUP BY day
        ORDER BY day ASC
    ''', (f'-{days} days',))
    
    receipt_items_by_day = {}
    for row in c.fetchall():
        receipt_items_by_day[row[0]] = {
            'items_count': float(row[1]),
            'items_sum': float(row[2])
        }
    
    # Собираем все даты
    all_dates = sorted(set(list(sales_by_day.keys()) + list(receipts_by_day.keys()) + 
                          list(sale_items_by_day.keys()) + list(receipt_items_by_day.keys())))
    
    daily_data = []
    for date in all_dates:
        s = sales_by_day.get(date, {})
        r = receipts_by_day.get(date, {})
        si = sale_items_by_day.get(date, {})
        ri = receipt_items_by_day.get(date, {})
        
        daily_data.append({
            'date': date,
            'sales': {
                'doc_count': s.get('doc_count', 0),
                'total_sum': s.get('total_sum', 0),
                'org_count': s.get('org_count', 0),
                'warehouse_count': s.get('warehouse_count', 0),
                'items_count': si.get('items_count', 0),
                'items_sum': si.get('items_sum', 0)
            },
            'receipts': {
                'doc_count': r.get('doc_count', 0),
                'total_sum': r.get('total_sum', 0),
                'org_count': r.get('org_count', 0),
                'warehouse_count': r.get('warehouse_count', 0),
                'items_count': ri.get('items_count', 0),
                'items_sum': ri.get('items_sum', 0)
            }
        })
    
    # Общая статистика за период
    total_sales_docs = sum(d['sales']['doc_count'] for d in daily_data)
    total_sales_sum = sum(d['sales']['total_sum'] for d in daily_data)
    total_sales_items = sum(d['sales']['items_count'] for d in daily_data)
    total_receipts_docs = sum(d['receipts']['doc_count'] for d in daily_data)
    total_receipts_sum = sum(d['receipts']['total_sum'] for d in daily_data)
    total_receipts_items = sum(d['receipts']['items_count'] for d in daily_data)
    
    # Топ-10 товаров по продажам
    c.execute('''
        SELECT 
            si.nomenclature_name,
            SUM(si.quantity) as total_qty,
            SUM(si.sum) as total_sum,
            COUNT(DISTINCT s.guid) as doc_count
        FROM sync_sale_items si
        JOIN sync_sales s ON s.guid = si.sale_guid
        GROUP BY si.nomenclature_name
        ORDER BY total_sum DESC
        LIMIT 10
    ''')
    
    top_sold = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    for item in top_sold:
        item['total_sum'] = float(item['total_sum'])
        item['total_qty'] = float(item['total_qty'])
    
    # Топ-10 товаров по приемкам
    c.execute('''
        SELECT 
            ri.nomenclature_name,
            SUM(ri.quantity) as total_qty,
            SUM(ri.sum) as total_sum,
            COUNT(DISTINCT r.guid) as doc_count
        FROM sync_receipt_items ri
        JOIN sync_receipts r ON r.guid = ri.receipt_guid
        GROUP BY ri.nomenclature_name
        ORDER BY total_sum DESC
        LIMIT 10
    ''')
    
    top_received = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    for item in top_received:
        item['total_sum'] = float(item['total_sum'])
        item['total_qty'] = float(item['total_qty'])
    
    db.close()
    
    return jsonify({
        'daily_data': daily_data,
        'summary': {
            'days': days,
            'sales': {
                'doc_count': total_sales_docs,
                'total_sum': total_sales_sum,
                'items_count': total_sales_items,
                'avg_per_day': round(total_sales_sum / days, 2) if days > 0 else 0
            },
            'receipts': {
                'doc_count': total_receipts_docs,
                'total_sum': total_receipts_sum,
                'items_count': total_receipts_items,
                'avg_per_day': round(total_receipts_sum / days, 2) if days > 0 else 0
            }
        },
        'top_sold': top_sold,
        'top_received': top_received
    })


# ==========================================
# API: Полная аналитика (маржа, ликвидность, остатки, ревизия)
# ==========================================

@sync_1c_bp.route('/analytics')
def get_analytics():
    """API: полная аналитика — маржинальность, ликвидность, остатки, ревизия"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    days_param = request.args.get('days', '30')
    if days_param == 'all':
        days_filter = ''
        days_num = 9999
    else:
        days = int(days_param)
        days = min(max(days, 7), 365)
        days_filter = f"WHERE date(s.date) >= date('now', '-{days} days')"
        days_num = days
    
    db = get_db_connection()
    c = db.cursor()
    
    # ===== 1. Ежедневные данные =====
    c.execute(f'''
        SELECT date(s.date) as day,
               COUNT(*) as sales_docs,
               COALESCE(SUM(s.total_sum), 0) as sales_sum,
               COALESCE(SUM(si.quantity), 0) as sales_items
        FROM sync_sales s
        LEFT JOIN sync_sale_items si ON s.guid = si.sale_guid
        {days_filter.replace('s.', 's.') if days_filter else ''}
        GROUP BY day ORDER BY day ASC
    ''')
    sales_by_day = {r[0]: {'doc_count': r[1], 'total_sum': float(r[2]), 'items_count': float(r[3])} for r in c.fetchall()}
    
    c.execute(f'''
        SELECT date(r.date) as day,
               COUNT(*) as receipts_docs,
               COALESCE(SUM(r.total_sum), 0) as receipts_sum,
               COALESCE(SUM(ri.quantity), 0) as receipts_items
        FROM sync_receipts r
        LEFT JOIN sync_receipt_items ri ON r.guid = ri.receipt_guid
        {days_filter.replace('s.', 'r.') if days_filter else ''}
        GROUP BY day ORDER BY day ASC
    ''')
    receipts_by_day = {r[0]: {'doc_count': r[1], 'total_sum': float(r[2]), 'items_count': float(r[3])} for r in c.fetchall()}
    
    all_dates = sorted(set(list(sales_by_day.keys()) + list(receipts_by_day.keys())))
    daily_data = []
    for date in all_dates:
        s = sales_by_day.get(date, {'doc_count': 0, 'total_sum': 0, 'items_count': 0})
        r = receipts_by_day.get(date, {'doc_count': 0, 'total_sum': 0, 'items_count': 0})
        margin_pct = round(((s['total_sum'] - r['total_sum']) / s['total_sum'] * 100) if s['total_sum'] > 0 else 0, 1)
        daily_data.append({
            'date': date, 'sales': s, 'receipts': r, 'margin_percent': margin_pct
        })
    
    # ===== 2. Маржинальность по товарам =====
    c.execute(f'''
        SELECT 
            si.nomenclature_name as name,
            SUM(si.quantity) as sold_qty,
            SUM(si.sum) as sold_sum,
            CASE WHEN SUM(si.quantity) > 0 THEN SUM(si.sum) / SUM(si.quantity) ELSE 0 END as avg_sale_price,
            COALESCE((
                SELECT CASE WHEN SUM(ri.quantity) > 0 THEN SUM(ri.sum) / SUM(ri.quantity) ELSE 0 END
                FROM sync_receipt_items ri
                JOIN sync_receipts r ON r.guid = ri.receipt_guid
                WHERE ri.nomenclature_name = si.nomenclature_name
            ), 0) as avg_purchase_price
        FROM sync_sale_items si
        JOIN sync_sales s ON s.guid = si.sale_guid
        GROUP BY si.nomenclature_name
        HAVING sold_qty > 0 AND avg_purchase_price > 0
        ORDER BY sold_sum DESC
    ''')
    
    margin_products = []
    margin_sum = {'products_with_margin': 0, 'total_products': 0, 'negative_margin_count': 0,
                  'avg_margin_percent': 0, 'max_margin_percent': 0, 'max_margin_product': ''}
    rows = c.fetchall()
    margin_sum['total_products'] = len(rows)
    total_margin_pct = 0
    for row in rows:
        name = row[0]; sold_qty = float(row[1] or 0); sold_sum = float(row[2] or 0)
        avg_sale = float(row[3] or 0); avg_purchase = float(row[4] or 0)
        margin_sum_r = sold_sum - (avg_purchase * sold_qty)
        margin_pct = round(((avg_sale - avg_purchase) / avg_purchase * 100) if avg_purchase > 0 else 0, 1)
        liquidity_score = min(100, int(sold_qty * 10))
        if margin_pct > 0: margin_sum['products_with_margin'] += 1
        if margin_pct < 0: margin_sum['negative_margin_count'] += 1
        if margin_pct > margin_sum['max_margin_percent']:
            margin_sum['max_margin_percent'] = margin_pct
            margin_sum['max_margin_product'] = name
        total_margin_pct += margin_pct
        margin_products.append({
            'name': name, 'sold_qty': sold_qty, 'sold_sum': sold_sum,
            'avg_sale_price': round(avg_sale, 2), 'avg_purchase_price': round(avg_purchase, 2),
            'margin_percent': margin_pct, 'margin_sum': round(margin_sum_r, 2),
            'liquidity_score': liquidity_score
        })
    margin_sum['avg_margin_percent'] = round(total_margin_pct / len(rows), 1) if rows else 0
    
    # ===== 3. Ликвидность =====
    c.execute(f'''
        SELECT 
            COALESCE(si.nomenclature_name, ri.nomenclature_name) as name,
            COALESCE(si.sold_qty, 0) as sold_qty,
            COALESCE(ri.received_qty, 0) as received_qty,
            COALESCE(ri.received_qty, 0) - COALESCE(si.sold_qty, 0) as stock_qty
        FROM (
            SELECT nomenclature_name, SUM(quantity) as sold_qty
            FROM sync_sale_items si2 JOIN sync_sales s2 ON s2.guid = si2.sale_guid
            GROUP BY si2.nomenclature_name
        ) si FULL OUTER JOIN (
            SELECT nomenclature_name, SUM(quantity) as received_qty
            FROM sync_receipt_items ri2 JOIN sync_receipts r2 ON r2.guid = ri2.receipt_guid
            GROUP BY ri2.nomenclature_name
        ) ri ON si.nomenclature_name = ri.nomenclature_name
        ORDER BY stock_qty DESC
    ''')
    
    liquidity_products = []
    liq_sum = {'high_liquidity': 0, 'medium_liquidity': 0, 'low_liquidity': 0, 'avg_turnover_days': 0}
    total_turnover = 0
    for row in c.fetchall():
        name = row[0]; sold_qty = float(row[1] or 0); received_qty = float(row[2] or 0); stock_qty = float(row[3] or 0)
        sales_per_day = round(sold_qty / days_num, 2) if days_num > 0 else 0
        days_in_stock = round(stock_qty / sales_per_day, 1) if sales_per_day > 0 else 999
        if sales_per_day >= 5: liquidity_score = 90; liq_sum['high_liquidity'] += 1
        elif sales_per_day >= 1: liquidity_score = 50; liq_sum['medium_liquidity'] += 1
        else: liquidity_score = 10; liq_sum['low_liquidity'] += 1
        if days_in_stock < 999: total_turnover += days_in_stock
        liquidity_products.append({
            'name': name, 'sold_qty': sold_qty, 'received_qty': received_qty,
            'stock_qty': stock_qty, 'days_in_stock': days_in_stock if days_in_stock < 999 else 0,
            'sales_per_day': sales_per_day, 'liquidity_score': liquidity_score
        })
    liq_sum['avg_turnover_days'] = round(total_turnover / len(liquidity_products), 1) if liquidity_products else 0
    
    # ===== 4. Товарный остаток =====
    c.execute(f'''
        SELECT 
            COALESCE(si.nomenclature_name, ri.nomenclature_name) as name,
            COALESCE(ri.received_qty, 0) as received_qty,
            COALESCE(si.sold_qty, 0) as sold_qty,
            COALESCE(ri.received_qty, 0) - COALESCE(si.sold_qty, 0) as stock_qty,
            COALESCE(ri.avg_price, 0) as avg_purchase_price,
            COALESCE(si.avg_price, 0) as avg_sale_price
        FROM (
            SELECT nomenclature_name, SUM(quantity) as sold_qty,
                   CASE WHEN SUM(quantity) > 0 THEN SUM(sum) / SUM(quantity) ELSE 0 END as avg_price
            FROM sync_sale_items si2 JOIN sync_sales s2 ON s2.guid = si2.sale_guid
            GROUP BY si2.nomenclature_name
        ) si FULL OUTER JOIN (
            SELECT nomenclature_name, SUM(quantity) as received_qty,
                   CASE WHEN SUM(quantity) > 0 THEN SUM(sum) / SUM(quantity) ELSE 0 END as avg_price
            FROM sync_receipt_items ri2 JOIN sync_receipts r2 ON r2.guid = ri2.receipt_guid
            GROUP BY ri2.nomenclature_name
        ) ri ON si.nomenclature_name = ri.nomenclature_name
        ORDER BY stock_qty DESC
    ''')
    
    stock_products = []
    st_sum = {'total_items': 0, 'total_sum': 0, 'normal_count': 0, 'negative_count': 0, 'negative_sum': 0, 'avg_stock_per_product': 0}
    for row in c.fetchall():
        name = row[0]; received_qty = float(row[1] or 0); sold_qty = float(row[2] or 0)
        stock_qty = float(row[3] or 0); avg_purchase = float(row[4] or 0); avg_sale = float(row[5] or 0)
        stock_sum = round(stock_qty * avg_purchase, 2)
        st_sum['total_items'] += stock_qty; st_sum['total_sum'] += stock_sum
        if stock_qty > 0: st_sum['normal_count'] += 1
        elif stock_qty < 0: st_sum['negative_count'] += 1; st_sum['negative_sum'] += abs(stock_sum)
        stock_products.append({
            'name': name, 'received_qty': received_qty, 'sold_qty': sold_qty,
            'stock_qty': stock_qty, 'stock_sum': stock_sum,
            'avg_purchase_price': round(avg_purchase, 2), 'avg_sale_price': round(avg_sale, 2)
        })
    st_sum['avg_stock_per_product'] = round(st_sum['total_items'] / len(stock_products), 1) if stock_products else 0
    
    # ===== 5. Ревизия =====
    revision_products = []
    rev_sum = {'match_count': 0, 'surplus_count': 0, 'shortage_count': 0,
               'surplus_sum': 0, 'shortage_sum': 0, 'total_checked': 0}
    for p in stock_products:
        expected = p['received_qty'] - p['sold_qty']
        actual = expected  # По умолчанию совпадает
        diff = actual - expected
        rev_sum['total_checked'] += 1
        if diff == 0: rev_sum['match_count'] += 1
        elif diff > 0: rev_sum['surplus_count'] += 1; rev_sum['surplus_sum'] += abs(diff * p['avg_purchase_price'])
        else: rev_sum['shortage_count'] += 1; rev_sum['shortage_sum'] += abs(diff * p['avg_purchase_price'])
        revision_products.append({
            'name': p['name'], 'expected_qty': expected, 'actual_qty': actual,
            'diff_qty': diff, 'diff_sum': round(diff * p['avg_purchase_price'], 2)
        })
    
    db.close()
    
    # ===== Сводка =====
    total_sales_sum = sum(d['sales']['total_sum'] for d in daily_data)
    total_receipts_sum = sum(d['receipts']['total_sum'] for d in daily_data)
    total_sales_items = sum(d['sales']['items_count'] for d in daily_data)
    total_receipts_items = sum(d['receipts']['items_count'] for d in daily_data)
    total_sales_docs = sum(d['sales']['doc_count'] for d in daily_data)
    total_receipts_docs = sum(d['receipts']['doc_count'] for d in daily_data)
    gross_profit = total_sales_sum - total_receipts_sum
    margin_percent = round((gross_profit / total_sales_sum * 100) if total_sales_sum > 0 else 0, 1)
    avg_markup = round(margin_sum['avg_margin_percent'], 1)
    products_in_trade = len(set(p['name'] for p in stock_products))
    products_sold = len(set(p['name'] for p in margin_products))
    
    return jsonify({
        'daily_data': daily_data,
        'summary': {
            'days': days_num,
            'sales': {'doc_count': total_sales_docs, 'total_sum': total_sales_sum, 'items_count': total_sales_items, 'avg_per_day': round(total_sales_sum / days_num, 2) if days_num > 0 else 0},
            'receipts': {'doc_count': total_receipts_docs, 'total_sum': total_receipts_sum, 'items_count': total_receipts_items, 'avg_per_day': round(total_receipts_sum / days_num, 2) if days_num > 0 else 0},
            'gross_profit': round(gross_profit, 2), 'margin_percent': margin_percent, 'avg_markup': avg_markup,
            'products_in_trade': products_in_trade, 'products_sold': products_sold,
            'stock_items_count': round(st_sum['total_items'], 1), 'stock_total_sum': round(st_sum['total_sum'], 2),
            'negative_stock_count': st_sum['negative_count'], 'turnover_days': liq_sum['avg_turnover_days']
        },
        'margin_summary': margin_sum, 'margin_products': margin_products,
        'liquidity_summary': liq_sum, 'liquidity_products': liquidity_products,
        'stock_summary': st_sum, 'stock_products': stock_products,
        'revision_summary': rev_sum, 'revision_products': revision_products
    })
