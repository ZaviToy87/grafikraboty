# -*- coding: utf-8 -*-
"""
web_barcodes.py — Штрих-коды API

Функции:
- Получение списка штрих-кодов
- Добавление штрих-кода
- Удаление штрих-кода
- Экспорт/импорт
"""
from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime
from web_config import logger, get_db_connection
import json
import io
import csv

barcodes_bp = Blueprint('barcodes', __name__)


@barcodes_bp.route('', methods=['GET'])
def get_barcodes():
    """Получить список штрих-кодов"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401

    search = request.args.get('search', '')
    limit = request.args.get('limit', type=int, default=100)
    offset = request.args.get('offset', type=int, default=0)

    db = get_db_connection()
    cursor = db.cursor()

    # Если есть поиск — загружаем ВСЕ записи и фильтруем в Python
    if search:
        search_lower = search.lower()
        
        # Загружаем ВСЕ активные штрих-коды (без пагинации для поиска)
        cursor.execute('''
            SELECT id, product_name, factory_barcode, internal_barcode,
                   created_by, created_at, is_active
            FROM barcodes
            WHERE is_active = 1
            ORDER BY product_name
        ''')
        
        all_barcodes = [dict(row) for row in cursor.fetchall()]
        
        # Фильтруем в Python (регистронезависимо)
        filtered_barcodes = [
            bc for bc in all_barcodes
            if search_lower in bc['product_name'].lower() or
               (bc['factory_barcode'] and search_lower in bc['factory_barcode'].lower()) or
               (bc['internal_barcode'] and search_lower in bc['internal_barcode'].lower())
        ]
        
        total = len(filtered_barcodes)
        
        # Применяем пагинацию к отфильтрованным
        start_idx = offset
        end_idx = offset + limit
        barcodes = filtered_barcodes[start_idx:end_idx]
    else:
        # Без поиска — просто пагинация
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM barcodes WHERE is_active = 1
        ''')
        total = cursor.fetchone()['cnt']
        
        cursor.execute('''
            SELECT id, product_name, factory_barcode, internal_barcode,
                   created_by, created_at, is_active
            FROM barcodes
            WHERE is_active = 1
            ORDER BY product_name
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        barcodes = [dict(row) for row in cursor.fetchall()]

    return jsonify({'status': 'success', 'barcodes': barcodes, 'total': total, 'count': len(barcodes)})


@barcodes_bp.route('/add', methods=['POST'])
def add_barcode():
    """Добавить штрих-код"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    data = request.json or {}
    product_name = data.get('product_name', '').strip()
    factory_barcode = data.get('factory_barcode', '').strip()
    internal_barcode = data.get('internal_barcode', '').strip()
    
    if not product_name:
        return jsonify({'status': 'error', 'message': 'Название товара обязательно'}), 400
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Проверяем дубликат только среди активных записей
    cursor.execute('''
        SELECT id FROM barcodes 
        WHERE is_active = 1
          AND ((factory_barcode = ? AND factory_barcode != '') 
           OR (internal_barcode = ? AND internal_barcode != ''))
    ''', (factory_barcode, internal_barcode))
    
    if cursor.fetchone():
        return jsonify({'status': 'error', 'message': 'Такой штрих-код уже существует'}), 400
    
    cursor.execute('''
        INSERT INTO barcodes 
        (product_name, factory_barcode, internal_barcode, created_by, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (product_name, factory_barcode or None, internal_barcode or None, 
          session['user_id'], datetime.now()))
    
    db.commit()
    
    barcode_id = cursor.lastrowid
    
    logger.info(f"Barcode added: id={barcode_id}, product={product_name}")
    
    return jsonify({
        'status': 'success',
        'message': 'Штрих-код добавлен',
        'id': barcode_id
    })


@barcodes_bp.route('/delete/<int:bid>', methods=['POST'])
def delete_barcode(bid):
    """Удалить штрих-код (мягкое удаление)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Мягкое удаление (is_active = 0)
    cursor.execute('''
        UPDATE barcodes SET is_active = 0 WHERE id = ?
    ''', (bid,))
    
    db.commit()
    
    logger.info(f"Barcode soft-deleted: id={bid}")
    
    return jsonify({'status': 'success', 'message': 'Штрих-код удалён'})


@barcodes_bp.route('/hard-delete/<int:bid>', methods=['POST'])
def hard_delete_barcode(bid):
    """Полностью удалить штрих-код из базы (только админ)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для администратора'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM barcodes WHERE id = ?', (bid,))
    db.commit()
    
    logger.info(f"Barcode hard-deleted: id={bid}")
    
    return jsonify({'status': 'success', 'message': 'Штрих-код полностью удалён из базы'})


@barcodes_bp.route('/cleanup-inactive', methods=['POST'])
def cleanup_inactive_barcodes():
    """Очистить все неактивные (удалённые) штрих-коды (только админ)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для администратора'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('SELECT COUNT(*) as cnt FROM barcodes WHERE is_active = 0')
    count = cursor.fetchone()['cnt']
    
    cursor.execute('DELETE FROM barcodes WHERE is_active = 0')
    db.commit()
    
    logger.info(f"Inactive barcodes cleaned up: {count} records deleted")
    
    return jsonify({
        'status': 'success', 
        'message': f'Очищено {count} неактивных штрих-кодов',
        'deleted_count': count
    })


@barcodes_bp.route('/inactive', methods=['GET'])
def get_inactive_barcodes():
    """Получить список неактивных (удалённых) штрих-кодов (только админ)"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для администратора'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT id, product_name, factory_barcode, internal_barcode,
               created_by, created_at, is_active
        FROM barcodes
        WHERE is_active = 0
        ORDER BY created_at DESC
    ''')
    
    barcodes = [dict(row) for row in cursor.fetchall()]
    
    return jsonify({'status': 'success', 'barcodes': barcodes, 'count': len(barcodes)})


@barcodes_bp.route('/export', methods=['GET'])
def export_barcodes():
    """Экспорт штрих-кодов в CSV"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT product_name, factory_barcode, internal_barcode, created_at
        FROM barcodes
        WHERE is_active = 1
        ORDER BY product_name
    ''')
    
    barcodes = cursor.fetchall()
    
    # Создаём CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Название товара', 'Заводской штрих-код', 'Внутренний штрих-код', 'Дата создания'])
    
    for row in barcodes:
        writer.writerow([row['product_name'], row['factory_barcode'] or '', 
                        row['internal_barcode'] or '', row['created_at'] or ''])
    
    output.seek(0)
    
    filename = f"barcodes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@barcodes_bp.route('/import', methods=['POST'])
def import_barcodes():
    """Импорт штрих-кодов из CSV"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Файл не загружен'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Файл не выбран'}), 400
    
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(content.splitlines())
        
        db = get_db_connection()
        cursor = db.cursor()
        
        imported = 0
        errors = []
        
        for i, row in enumerate(reader, 1):
            try:
                product_name = row.get('Название товара', row.get('product_name', '')).strip()
                factory_barcode = row.get('Заводской штрих-код', row.get('factory_barcode', '')).strip()
                internal_barcode = row.get('Внутренний штрих-код', row.get('internal_barcode', '')).strip()
                
                if not product_name:
                    errors.append(f"Строка {i}: нет названия товара")
                    continue
                
                # Проверяем дубликат только среди активных записей
                cursor.execute('''
                    SELECT id FROM barcodes 
                    WHERE is_active = 1
                      AND ((factory_barcode = ? AND factory_barcode != '') 
                       OR (internal_barcode = ? AND internal_barcode != ''))
                ''', (factory_barcode, internal_barcode))
                
                if cursor.fetchone():
                    errors.append(f"Строка {i}: дубликат штрих-кода")
                    continue
                
                cursor.execute('''
                    INSERT INTO barcodes 
                    (product_name, factory_barcode, internal_barcode, created_by, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (product_name, factory_barcode or None, internal_barcode or None,
                      session['user_id'], datetime.now()))
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Строка {i}: {str(e)}")
        
        db.commit()
        
        logger.info(f"Barcodes imported: {imported} items")
        
        return jsonify({
            'status': 'success',
            'message': f'Импортировано {imported} штрих-кодов',
            'imported': imported,
            'errors': errors
        })
        
    except Exception as e:
        logger.exception(f"Barcode import error: {e}")
        return jsonify({'status': 'error', 'message': f'Ошибка импорта: {str(e)}'}), 500
