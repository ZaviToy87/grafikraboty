# -*- coding: utf-8 -*-
"""
web_com_scanner.py — API для работы с COM-сканерами штрих-кодов
"""
from flask import Blueprint, jsonify, request
from com_scanner import add_barcode_callback, get_last_barcode, clear_last_barcode
import threading

com_scanner_bp = Blueprint('com_scanner', __name__)

# Очередь последних штрих-кодов
barcode_queue = []
queue_lock = threading.Lock()


def on_barcode_scanned(barcode, scanner_name):
    """Обработчик сканирования — добавляет в очередь"""
    with queue_lock:
        barcode_queue.append({
            'barcode': barcode,
            'scanner': scanner_name,
            'timestamp': get_last_barcode().get('timestamp')
        })
        
        # Держим только последние 10
        if len(barcode_queue) > 10:
            barcode_queue.pop(0)


# Регистрируем обработчик
add_barcode_callback(on_barcode_scanned)


@com_scanner_bp.route('/last', methods=['GET'])
def get_last():
    """Получить последний отсканированный штрих-код"""
    return jsonify({
        'status': 'success',
        'data': get_last_barcode()
    })


@com_scanner_bp.route('/queue', methods=['GET'])
def get_queue():
    """Получить очередь последних штрих-кодов"""
    with queue_lock:
        return jsonify({
            'status': 'success',
            'queue': list(barcode_queue)
        })


@com_scanner_bp.route('/clear', methods=['POST'])
def clear():
    """Очистить очередь и последний штрих-код"""
    clear_last_barcode()
    with queue_lock:
        barcode_queue.clear()

    return jsonify({
        'status': 'success',
        'message': 'Очередь очищена'
    })


@com_scanner_bp.route('/status', methods=['GET'])
def status():
    """Статус COM-сканеров"""
    from com_scanner import COM_PORTS, scanners_enabled

    return jsonify({
        'status': 'success',
        'enabled': scanners_enabled,
        'scanners': [
            {
                'name': config['name'],
                'port': config['port'],
                'baudrate': config['baudrate']
            }
            for config in COM_PORTS.values()
        ],
        'last_barcode': get_last_barcode()
    })


@com_scanner_bp.route('/enable', methods=['POST'])
def enable():
    """Включить сканеры"""
    from com_scanner import enable_scanners, get_scanners_status
    
    success = enable_scanners()
    
    return jsonify({
        'status': 'success' if success else 'already_enabled',
        'message': 'Сканеры включены' if success else 'Сканеры уже включены',
        'data': get_scanners_status()
    })


@com_scanner_bp.route('/disable', methods=['POST'])
def disable():
    """Выключить сканеры"""
    from com_scanner import disable_scanners, get_scanners_status
    
    success = disable_scanners()
    
    return jsonify({
        'status': 'success' if success else 'already_disabled',
        'message': 'Сканеры выключены' if success else 'Сканеры уже выключены',
        'data': get_scanners_status()
    })


@com_scanner_bp.route('/toggle', methods=['POST'])
def toggle():
    """Переключить состояние сканеров"""
    from com_scanner import enable_scanners, disable_scanners, scanners_enabled, get_scanners_status
    
    if scanners_enabled:
        success = disable_scanners()
        message = 'Сканеры выключены'
    else:
        success = enable_scanners()
        message = 'Сканеры включены'
    
    return jsonify({
        'status': 'success',
        'enabled': scanners_enabled,
        'message': message,
        'data': get_scanners_status()
    })
