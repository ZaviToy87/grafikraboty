# -*- coding: utf-8 -*-
"""
web_products_1c.py — API для справочника товаров из 1С
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sqlite3
from web_config import get_db_connection

products_1c_bp = Blueprint('products_1c', __name__)


@products_1c_bp.route('/search', methods=['GET'])
def search_products():
    """
    Поиск товара по штрих-коду или названию
    Параметры:
    - barcode (приоритет) — точное совпадение штрих-кода
    - query — поиск по названию
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    barcode = request.args.get('barcode', '').strip()
    query = request.args.get('query', '').strip()
    limit = int(request.args.get('limit', 20))
    
    db = get_db_connection()
    cursor = db.cursor()
    
    results = []
    
    # Поиск по штрих-коду (приоритет)
    if barcode:
        cursor.execute('''
            SELECT * FROM products_1c
            WHERE barcode_main = ? OR barcode_inner = ?
            LIMIT ?
        ''', (barcode, barcode, limit))
        
        for row in cursor.fetchall():
            results.append(dict(row))
    
    # Поиск по названию
    if query and not results:
        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT * FROM products_1c
            WHERE name LIKE ? OR full_name LIKE ? OR vendor_code LIKE ?
            LIMIT ?
        ''', (search_pattern, search_pattern, search_pattern, limit))
        
        for row in cursor.fetchall():
            results.append(dict(row))
    
    db.close()
    
    return jsonify({
        'status': 'success',
        'count': len(results),
        'products': results
    })


@products_1c_bp.route('/barcode/<barcode>', methods=['GET'])
def get_product_by_barcode(barcode):
    """Получить товар по штрих-коду"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    db = get_db_connection()
    cursor = db.cursor()

    # Ищем точное совпадение или частичное
    cursor.execute('''
        SELECT * FROM products_1c
        WHERE barcode_main = ? OR barcode_inner = ? OR barcode_main LIKE ? OR barcode_inner LIKE ?
        LIMIT 1
    ''', (barcode, barcode, f'%{barcode}%', f'%{barcode}%'))

    row = cursor.fetchone()
    db.close()

    if row:
        return jsonify({
            'status': 'success',
            'product': dict(row)
        })
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Товар по штрих-коду не найден'
        }), 404


@products_1c_bp.route('', methods=['GET'])
def get_all_products():
    """Получить все товары (с фильтрацией)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Фильтры
    group = request.args.get('group')
    search = request.args.get('search')
    limit = int(request.args.get('limit', 100))
    
    query = 'SELECT * FROM products_1c WHERE is_active = 1'
    params = []
    
    if group:
        query += ' AND group_name = ?'
        params.append(group)
    
    if search:
        query += ' AND (name LIKE ? OR barcode_main LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += ' ORDER BY name LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    
    products = [dict(row) for row in cursor.fetchall()]
    
    # Получаем список групп
    cursor.execute('SELECT DISTINCT group_name FROM products_1c WHERE group_name IS NOT NULL ORDER BY group_name')
    groups = [row[0] for row in cursor.fetchall()]
    
    db.close()
    
    return jsonify({
        'status': 'success',
        'count': len(products),
        'products': products,
        'groups': groups
    })


@products_1c_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Обновить товар (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    data = request.json or {}
    
    db = get_db_connection()
    cursor = db.cursor()
    
    updates = []
    params = []
    
    if 'name' in data:
        updates.append('name = ?')
        params.append(data['name'])
    
    if 'retail_price' in data:
        updates.append('retail_price = ?')
        params.append(float(data['retail_price']))
    
    if 'barcode_main' in data:
        updates.append('barcode_main = ?')
        params.append(data['barcode_main'])
    
    if 'barcode_inner' in data:
        updates.append('barcode_inner = ?')
        params.append(data['barcode_inner'])
    
    if 'group_name' in data:
        updates.append('group_name = ?')
        params.append(data['group_name'])
    
    if not updates:
        db.close()
        return jsonify({'status': 'error', 'message': 'Нет данных для обновления'}), 400
    
    updates.append('updated_at = ?')
    params.append(datetime.now())
    params.append(product_id)
    
    cursor.execute(f'''
        UPDATE products_1c
        SET {', '.join(updates)}
        WHERE id = ?
    ''', params)
    
    db.commit()
    db.close()
    
    return jsonify({
        'status': 'success',
        'message': 'Товар обновлён'
    })


@products_1c_bp.route('/import', methods=['POST'])
def import_products():
    """Импортировать товары из Excel файлов 1С"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    try:
        # Запускаем скрипт импорта
        import import_1c_products
        result = import_1c_products.load_products_from_excel(update_existing=True)
        
        return jsonify({
            'status': 'success',
            'imported': result['imported'],
            'updated': result['updated'],
            'errors': result['errors']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
