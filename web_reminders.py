# -*- coding: utf-8 -*-
"""
web_reminders.py — Модуль напоминаний с подтверждением
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import sqlite3
from web_config import logger, get_db_connection
import vk_bot

reminders_bp = Blueprint('reminders', __name__)


@reminders_bp.route('', methods=['GET'])
def get_active_reminders():
    """Получить активные напоминания для пользователя"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    user_id = session['user_id']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Получаем все активные напоминания
    cursor.execute('''
        SELECT r.*, 
               CASE WHEN rc.id IS NOT NULL THEN 1 ELSE 0 END as is_confirmed
        FROM reminders r
        LEFT JOIN reminder_confirmations rc ON r.id = rc.reminder_id AND rc.user_id = ?
        WHERE r.is_active = 1
          AND (r.expires_at IS NULL OR r.expires_at > ?)
        ORDER BY r.created_at DESC
    ''', (user_id, datetime.now()))
    
    reminders = []
    for row in cursor.fetchall():
        rem = dict(row)
        
        # Получаем статистику подтверждений
        cursor.execute('''
            SELECT COUNT(*) as total, SUM(CASE WHEN confirmed_at IS NOT NULL THEN 1 ELSE 0 END) as confirmed
            FROM reminder_confirmations
            WHERE reminder_id = ?
        ''', (rem['id'],))
        
        stats = dict(cursor.fetchone())
        rem['total_users'] = stats['total'] or 0
        rem['confirmed_users'] = stats['confirmed'] or 0
        
        reminders.append(rem)
    
    db.close()
    
    return jsonify({'status': 'success', 'reminders': reminders})


@reminders_bp.route('/<int:reminder_id>/confirm', methods=['POST'])
def confirm_reminder(reminder_id):
    """Пользователь подтверждает прочтение напоминания"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    user_id = session['user_id']
    full_name = session.get('full_name', 'Unknown')
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Проверяем существует ли напоминание
    cursor.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,))
    reminder = cursor.fetchone()
    
    if not reminder:
        db.close()
        return jsonify({'status': 'error', 'message': 'Напоминание не найдено'}), 404
    
    # Проверяем не подтверждал ли уже
    cursor.execute('''
        SELECT id FROM reminder_confirmations
        WHERE reminder_id = ? AND user_id = ?
    ''', (reminder_id, user_id))
    
    existing = cursor.fetchone()
    
    if not existing:
        # Записываем подтверждение
        cursor.execute('''
            INSERT INTO reminder_confirmations (reminder_id, user_id, confirmed_at)
            VALUES (?, ?, ?)
        ''', (reminder_id, user_id, datetime.now()))
        
        db.commit()
        
        logger.info(f"Reminder {reminder_id} confirmed by {full_name} (user {user_id})")
        
        # Проверяем все ли подтвердили
        cursor.execute('''
            SELECT r.total_users, COUNT(rc.id) as confirmed_count
            FROM reminders r
            LEFT JOIN reminder_confirmations rc ON r.id = rc.reminder_id
            WHERE r.id = ?
            GROUP BY r.id
        ''', (reminder_id,))
        
        result = dict(cursor.fetchone())
        
        # Если все подтвердили — можно отправить отчёт админу
        if result['confirmed_count'] >= result['total_users'] and result['total_users'] > 0:
            send_confirmation_report_to_admin(reminder_id, cursor)
            db.commit()
    else:
        logger.info(f"Reminder {reminder_id} already confirmed by {full_name}")
    
    db.close()
    
    return jsonify({'status': 'success', 'message': 'Подтверждено'})


@reminders_bp.route('', methods=['POST'])
def create_reminder():
    """Создать напоминание (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    data = request.json or {}
    
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()
    reminder_type = data.get('type', 'general')
    require_confirmation = data.get('require_confirmation', True)
    expires_hours = data.get('expires_hours')  # Через сколько часов истечёт
    
    if not title or not message:
        return jsonify({'status': 'error', 'message': 'Заголовок и текст обязательны'}), 400
    
    # Определяем срок действия
    expires_at = None
    if expires_hours:
        expires_at = datetime.now() + timedelta(hours=int(expires_hours))
    
    # Считаем сколько всего пользователей
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE role != "admin"')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('''
        INSERT INTO reminders
        (title, message, created_by, reminder_type, require_confirmation, expires_at, total_users)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        title,
        message,
        session['user_id'],
        reminder_type,
        1 if require_confirmation else 0,
        expires_at,
        total_users
    ))
    
    db.commit()
    reminder_id = cursor.lastrowid
    
    logger.info(f"Reminder created: id={reminder_id}, title={title}, type={reminder_type}")
    
    # Отправляем уведомление в VK чат
    send_reminder_to_vk(title, message, reminder_id)
    
    db.close()
    
    return jsonify({
        'status': 'success',
        'message': 'Напоминание создано',
        'reminder_id': reminder_id
    })


@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Удалить напоминание (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('UPDATE reminders SET is_active = 0 WHERE id = ?', (reminder_id,))
    db.commit()
    db.close()
    
    logger.info(f"Reminder {reminder_id} deactivated by admin")
    
    return jsonify({'status': 'success', 'message': 'Напоминание удалено'})


@reminders_bp.route('/<int:reminder_id>/stats', methods=['GET'])
def get_reminder_stats(reminder_id):
    """Статистика подтверждений напоминания (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Общая статистика
    cursor.execute('''
        SELECT r.*, u.full_name as creator_name
        FROM reminders r
        JOIN users u ON r.created_by = u.id
        WHERE r.id = ?
    ''', (reminder_id,))
    
    reminder = dict(cursor.fetchone())
    
    # Кто подтвердил
    cursor.execute('''
        SELECT u.id, u.full_name, u.role, rc.confirmed_at
        FROM reminder_confirmations rc
        JOIN users u ON rc.user_id = u.id
        WHERE rc.reminder_id = ?
        ORDER BY rc.confirmed_at DESC
    ''', (reminder_id,))
    
    confirmed = [dict(row) for row in cursor.fetchall()]
    
    # Кто НЕ подтвердил
    cursor.execute('''
        SELECT u.id, u.full_name, u.role
        FROM users u
        WHERE u.role != 'admin'
          AND u.id NOT IN (
              SELECT user_id FROM reminder_confirmations WHERE reminder_id = ?
          )
    ''', (reminder_id,))
    
    not_confirmed = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return jsonify({
        'status': 'success',
        'reminder': reminder,
        'confirmed': confirmed,
        'not_confirmed': not_confirmed,
        'progress': f"{len(confirmed)}/{reminder['total_users']}"
    })


def send_reminder_to_vk(title, message, reminder_id):
    """Отправить напоминание в VK чат"""
    config = vk_bot.get_config()
    chat_peer_id = config.get('chat_peer_id')
    
    if not chat_peer_id:
        logger.warning("VK chat_peer_id not configured")
        return
    
    msg = (
        f"📢 *НОВОЕ НАПОМИНАНИЕ*\n\n"
        f"📌 *{title}*\n\n"
        f"{message}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Требуется подтверждение!*\n"
        f"Откройте программу и нажмите «Прочитано»\n\n"
        f"ID: {reminder_id}"
    )
    
    vk_bot.send_message(peer_id=chat_peer_id, message=msg)
    logger.info(f"Reminder {reminder_id} sent to VK chat")


def send_confirmation_report_to_admin(reminder_id, cursor=None):
    """Отправить админу отчёт что все подтвердили"""
    close_db = False
    if cursor is None:
        db = get_db_connection()
        cursor = db.cursor()
        close_db = True
    
    cursor.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,))
    reminder = cursor.fetchone()
    
    if not reminder:
        if close_db:
            db.close()
        return
    
    # Получаем список кто подтвердил
    cursor.execute('''
        SELECT u.full_name, rc.confirmed_at
        FROM reminder_confirmations rc
        JOIN users u ON rc.user_id = u.id
        WHERE rc.reminder_id = ?
        ORDER BY rc.confirmed_at
    ''', (reminder_id,))
    
    confirmed_list = cursor.fetchall()
    
    if close_db:
        db.close()
    
    config = vk_bot.get_config()
    admin_vk_id = config.get('admin_vk_id')
    
    if not admin_vk_id:
        return
    
    msg = (
        f"✅ *ВСЕ ПОДТВЕРДИЛИ!*\n\n"
        f"📌 *{reminder['title']}*\n\n"
        f"Все сотрудники ({len(confirmed_list)} чел.) подтвердили прочтение.\n\n"
        f"📋 *Список:*\n"
    )
    
    for name, confirmed_at in confirmed_list:
        msg += f"• {name} — {confirmed_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    vk_bot.send_message(peer_id=admin_vk_id, message=msg)
    logger.info(f"Confirmation report for reminder {reminder_id} sent to admin")


def create_revision_reminder(product_name, expiry_date, cursor=None):
    """Создать автоматическое напоминание о просрочке товара"""
    close_db = False
    if cursor is None:
        db = get_db_connection()
        cursor = db.cursor()
        close_db = True
    
    title = f"⚠️ Просрочка: {product_name}"
    message = (
        f"Товар «{product_name}» просрочен ({expiry_date}).\n\n"
        f"Необходимо:\n"
        f"1. Проверить наличие в холодильнике\n"
        f"2. Утилизировать или вернуть поставщику\n"
        f"3. Отметить в системе"
    )
    
    # Считаем пользователей
    cursor.execute('SELECT COUNT(*) FROM users WHERE role != "admin"')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('''
        INSERT INTO reminders
        (title, message, reminder_type, require_confirmation, total_users, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        title,
        message,
        'revision',
        1,
        total_users,
        datetime.now() + timedelta(days=7)  # Действует неделю
    ))
    
    db.commit()
    reminder_id = cursor.lastrowid
    
    if close_db:
        db.close()
    
    logger.info(f"Auto revision reminder created: {reminder_id}")
    
    # Отправляем в VK
    send_reminder_to_vk(title, message, reminder_id)
    
    return reminder_id
