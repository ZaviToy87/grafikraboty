# -*- coding: utf-8 -*-
"""
web_notifications.py — Система уведомлений (Notification Center)
API: /api/notifications/*
v2.0 — Добавлен Socket.IO real-time + звуковые оповещения
"""
from flask import Blueprint, request, jsonify, session
from web_config import get_db_connection, logger
from datetime import datetime
import json

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Ссылка на socketio будет установлена из web_server
_socketio = None

def init_socketio(socketio_instance):
    """Инициализировать Socket.IO для real-time уведомлений"""
    global _socketio
    _socketio = socketio_instance

def create_notifications_table():
    """Создать таблицу уведомлений если её нет"""
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL DEFAULT 'info',
            title TEXT NOT NULL,
            message TEXT,
            link TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, is_read)')
    db.commit()
    db.close()

def add_notification(user_id, type, title, message=None, link=None):
    """Добавить уведомление для пользователя + real-time через Socket.IO"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO notifications (user_id, type, title, message, link) VALUES (?, ?, ?, ?, ?)',
            (user_id, type, title, message, link)
        )
        db.commit()
        notif_id = cursor.lastrowid
        db.close()

        # Real-time уведомление через Socket.IO
        if _socketio:
            _socketio.emit('new_notification', {
                'id': notif_id,
                'user_id': user_id,
                'type': type,
                'title': title,
                'message': message,
                'link': link,
                'is_read': 0,
                'created_at': datetime.now().isoformat()
            }, room=f'user_{user_id}')

        return True
    except Exception as e:
        logger.error(f"Error adding notification: {e}")
        return False

def add_notification_all(type, title, message=None, link=None):
    """Добавить уведомление для всех пользователей + real-time"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE is_active = 1 OR is_active IS NULL')
        users = cursor.fetchall()
        for user in users:
            cursor.execute(
                'INSERT INTO notifications (user_id, type, title, message, link) VALUES (?, ?, ?, ?, ?)',
                (user['id'], type, title, message, link)
            )
            notification_id = cursor.lastrowid
            # Real-time для каждого пользователя
            if _socketio:
                _socketio.emit('new_notification', {
                    'id': notification_id,
                    'type': type,
                    'title': title,
                    'message': message,
                    'link': link,
                    'is_read': 0,
                    'created_at': datetime.now().isoformat()
                }, room=f'user_{user["id"]}')
        db.commit()
        db.close()
        return True
    except Exception as e:
        logger.error(f"Error adding notification to all: {e}")
        return False


@notifications_bp.route('/list')
def get_notifications():
    """Получить уведомления пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    user_id = session['user_id']
    limit = request.args.get('limit', 50, type=int)
    unread_only = request.args.get('unread_only', 0, type=int)
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        if unread_only:
            cursor.execute(
                'SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC LIMIT ?',
                (user_id, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                (user_id, limit)
            )
        
        notifications = [dict(row) for row in cursor.fetchall()]
        
        # Получить количество непрочитанных
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0',
            (user_id,)
        )
        unread_count = cursor.fetchone()['cnt']
        
        db.close()
        
        return jsonify({
            'status': 'success',
            'notifications': notifications,
            'unread_count': unread_count
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/read/<int:notification_id>', methods=['POST'])
def mark_read(notification_id):
    """Отметить уведомление как прочитанное"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?',
            (notification_id, session['user_id'])
        )
        db.commit()
        db.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/read-all', methods=['POST'])
def mark_all_read():
    """Отметить все уведомления как прочитанные"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE notifications SET is_read = 1 WHERE user_id = ?',
            (session['user_id'],)
        )
        db.commit()
        db.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/delete/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Удалить уведомление"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            'DELETE FROM notifications WHERE id = ? AND user_id = ?',
            (notification_id, session['user_id'])
        )
        db.commit()
        db.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/clear', methods=['POST'])
def clear_all():
    """Очистить все уведомления пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            'DELETE FROM notifications WHERE user_id = ?',
            (session['user_id'],)
        )
        db.commit()
        db.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/unread-count')
def unread_count():
    """Получить количество непрочитанных уведомлений"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            'SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0',
            (session['user_id'],)
        )
        count = cursor.fetchone()['cnt']
        db.close()
        return jsonify({'status': 'success', 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
