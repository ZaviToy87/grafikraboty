# -*- coding: utf-8 -*-
"""
smart_revision_system.py — Умная система статистики и напоминаний для ревизии товаров

Система включает:
1. Расширенную статистику по всем типам операций
2. Умные напоминания с триггерами
3. Автоматические уведомления в VK чат
4. Персональные напоминания для продавцов
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import sqlite3
import json
from web_config import logger, get_db_connection
import vk_bot

smart_bp = Blueprint('smart_revision', __name__)

# Конфигурация умных напоминаний
REMINDER_CONFIG = {
    'expiring_soon_days': 7,           # Напоминать за 7 дней до истечения
    'high_discount_threshold': 40,     # Скидка 40%+ считается высокой
    'stale_days': 14,                  # Товар считается "залежавшимся" если не продается 14 дней
    'daily_check_hour': 9,             # Ежедневная проверка в 9:00
    'weekly_report_day': 0,            # 0=Понедельник, еженедельный отчет
}

# Категории операций для статистики
OPERATION_CATEGORIES = {
    'sales': ['sold', 'sold_discount', 'sold_promo'],
    'write_offs': ['written_off_expired', 'written_off_damaged', 'written_off_lost'],
    'personal_use': ['taken_personal', 'taken_gift', 'taken_test'],
    'returns_exchanges': ['returned_supplier', 'exchanged_supplier', 'exchanged_customer', 'returned_customer'],
    'transfers': ['transferred_store', 'transferred_branch'],
    'other': ['utilized', 'donated'],
    'price_changes': ['price_increased', 'price_decreased']
}

def get_smart_stats(user_id=None, period_days=30):
    """
    Получить расширенную статистику за период
    period_days: 7, 30, 90 или None (все время)
    """
    db = get_db_connection()
    cursor = db.cursor()
    
    # Базовые условия
    where_conditions = []
    params = []
    
    if period_days:
        date_from = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        where_conditions.append("t.created_at >= ?")
        params.append(date_from)
    
    if user_id:
        where_conditions.append("t.user_id = ?")
        params.append(user_id)
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # 1. Общая статистика по операциям
    cursor.execute(f'''
        SELECT 
            COUNT(*) as total_operations,
            SUM(CASE WHEN t.action IN ('sold', 'sold_discount', 'sold_promo') THEN t.quantity ELSE 0 END) as total_sold_qty,
            SUM(CASE WHEN t.action IN ('sold', 'sold_discount', 'sold_promo') THEN t.price * t.quantity ELSE 0 END) as total_revenue,
            SUM(CASE WHEN t.action IN ('written_off_expired', 'written_off_damaged', 'written_off_lost') THEN t.quantity ELSE 0 END) as total_written_off_qty,
            SUM(CASE WHEN t.action IN ('written_off_expired', 'written_off_damaged', 'written_off_lost') THEN t.price * t.quantity ELSE 0 END) as total_write_off_value,
            SUM(CASE WHEN t.action IN ('taken_personal', 'taken_gift', 'taken_test') THEN t.quantity ELSE 0 END) as total_personal_qty,
            SUM(CASE WHEN t.action IN ('taken_personal', 'taken_gift', 'taken_test') THEN t.price * t.quantity ELSE 0 END) as total_personal_value
        FROM revision_transactions t
        {where_clause}
    ''', params)
    
    general_stats = dict(cursor.fetchone())
    
    # 2. Статистика по типам операций
    cursor.execute(f'''
        SELECT 
            t.action,
            COUNT(*) as operation_count,
            SUM(t.quantity) as total_quantity,
            SUM(t.price * t.quantity) as total_value,
            AVG(t.price) as avg_price
        FROM revision_transactions t
        {where_clause}
        GROUP BY t.action
        ORDER BY total_quantity DESC
    ''', params)
    
    by_action = [dict(row) for row in cursor.fetchall()]
    
    # 3. Статистика по сотрудникам (топ 10)
    cursor.execute(f'''
        SELECT 
            t.user_id,
            u.full_name,
            COUNT(*) as total_operations,
            SUM(CASE WHEN t.action IN ('sold', 'sold_discount', 'sold_promo') THEN t.quantity ELSE 0 END) as sold_qty,
            SUM(CASE WHEN t.action IN ('sold', 'sold_discount', 'sold_promo') THEN t.price * t.quantity ELSE 0 END) as revenue,
            SUM(CASE WHEN t.action IN ('written_off_expired', 'written_off_damaged', 'written_off_lost') THEN t.quantity ELSE 0 END) as write_off_qty,
            SUM(CASE WHEN t.action IN ('written_off_expired', 'written_off_damaged', 'written_off_lost') THEN t.price * t.quantity ELSE 0 END) as write_off_value,
            MAX(t.created_at) as last_operation
        FROM revision_transactions t
        LEFT JOIN users u ON t.user_id = u.id
        {where_clause}
        GROUP BY t.user_id, u.full_name
        ORDER BY revenue DESC
        LIMIT 10
    ''', params)
    
    top_employees = [dict(row) for row in cursor.fetchall()]
    
    # 4. Статистика по товарам (топ 10 по продажам)
    cursor.execute(f'''
        SELECT 
            r.product_name,
            r.barcode,
            SUM(CASE WHEN t.action IN ('sold', 'sold_discount', 'sold_promo') THEN t.quantity ELSE 0 END) as sold_qty,
            SUM(CASE WHEN t.action IN ('sold', 'sold_discount', 'sold_promo') THEN t.price * t.quantity ELSE 0 END) as revenue,
            SUM(CASE WHEN t.action IN ('written_off_expired', 'written_off_damaged', 'written_off_lost') THEN t.quantity ELSE 0 END) as write_off_qty,
            MIN(r.created_at) as first_added,
            MAX(t.created_at) as last_operation
        FROM revision_transactions t
        LEFT JOIN product_revisions r ON t.revision_id = r.id
        {where_clause}
        GROUP BY r.product_name, r.barcode
        HAVING sold_qty > 0 OR write_off_qty > 0
        ORDER BY revenue DESC
        LIMIT 10
    ''', params)
    
    top_products = [dict(row) for row in cursor.fetchall()]
    
    # 5. Эффективность (продажи vs списания)
    # Handle None values from database
    total_sold_qty = general_stats.get('total_sold_qty') or 0
    total_written_off_qty = general_stats.get('total_written_off_qty') or 0
    total_personal_qty = general_stats.get('total_personal_qty') or 0
    
    total_items = total_sold_qty + total_written_off_qty
    if total_items > 0:
        sales_efficiency = (total_sold_qty / total_items) * 100
    else:
        sales_efficiency = 0
    
    efficiency_stats = {
        'sales_efficiency_percent': round(sales_efficiency, 1),
        'total_items': total_items,
        'sold_items': total_sold_qty,
        'written_off_items': total_written_off_qty,
        'personal_items': total_personal_qty
    }
    
    # 6. Текущее состояние ревизии
    cursor.execute('''
        SELECT 
            COUNT(*) as total_active,
            SUM(CASE WHEN days_remaining < 0 THEN 1 ELSE 0 END) as expired,
            SUM(CASE WHEN days_remaining BETWEEN 0 AND 7 THEN 1 ELSE 0 END) as expiring_soon,
            SUM(CASE WHEN discount_percent >= 40 THEN 1 ELSE 0 END) as high_discount,
            SUM(CASE WHEN status = 'admin_decision' THEN 1 ELSE 0 END) as need_decision,
            SUM(retail_price) as total_value,
            SUM(final_price) as total_final_value
        FROM product_revisions
        WHERE status IN ('active', 'admin_decision')
    ''')
    
    current_state = dict(cursor.fetchone())
    
    db.close()
    
    return {
        'general': general_stats,
        'by_action': by_action,
        'top_employees': top_employees,
        'top_products': top_products,
        'efficiency': efficiency_stats,
        'current_state': current_state,
        'period_days': period_days
    }

def check_smart_reminders():
    """
    Проверить и создать умные напоминания
    Возвращает список созданных напоминаний
    """
    db = get_db_connection()
    cursor = db.cursor()
    created_reminders = []
    
    today = datetime.now().date()
    
    # 1. Товары, которые скоро истекают (за 7 дней)
    cursor.execute('''
        SELECT r.*, u.vk_id
        FROM product_revisions r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.status = 'active'
          AND r.days_remaining BETWEEN 0 AND ?
          AND r.expiry_reminder_sent = 0
    ''', (REMINDER_CONFIG['expiring_soon_days'],))
    
    expiring_soon = cursor.fetchall()
    
    for rev in expiring_soon:
        # Создаем напоминание
        reminder_id = create_smart_reminder(
            cursor=cursor,
            revision_id=rev['id'],
            user_id=rev['user_id'],
            reminder_type='expiring_soon',
            title=f"Товар скоро истекает: {rev['product_name']}",
            message=f"Срок годности истекает через {rev['days_remaining']} дней ({rev['expiry_date']}). Цена со скидкой: {rev['final_price']:.2f} ₽",
            priority='medium'
        )
        
        if reminder_id:
            created_reminders.append(reminder_id)
            cursor.execute('UPDATE product_revisions SET expiry_reminder_sent = 1 WHERE id = ?', (rev['id'],))
            
            # Отправляем уведомление в VK
            send_vk_reminder(
                user_vk_id=rev['vk_id'],
                title="Товар скоро истекает",
                message=f"📦 {rev['product_name']}\n⏰ Истекает через {rev['days_remaining']} дней\n💰 Цена: {rev['final_price']:.2f} ₽"
            )
    
    # 2. Товары с большой скидкой, которые не продаются
    cursor.execute('''
        SELECT r.*, u.vk_id,
               (SELECT MAX(created_at) FROM revision_transactions WHERE revision_id = r.id) as last_operation
        FROM product_revisions r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.status = 'active'
          AND r.discount_percent >= ?
          AND (r.last_sale_reminder IS NULL OR date(r.last_sale_reminder) < date('now', '-7 days'))
          AND (r.last_operation IS NULL OR date(r.last_operation) < date('now', ?))
    ''', (REMINDER_CONFIG['high_discount_threshold'], f"-{REMINDER_CONFIG['stale_days']} days"))
    
    stale_high_discount = cursor.fetchall()
    
    for rev in stale_high_discount:
        days_stale = (today - datetime.strptime(rev['last_operation'] or rev['created_at'], '%Y-%m-%d %H:%M:%S').date()).days if rev['last_operation'] else (today - datetime.strptime(rev['created_at'], '%Y-%m-%d %H:%M:%S').date()).days
        
        reminder_id = create_smart_reminder(
            cursor=cursor,
            revision_id=rev['id'],
            user_id=rev['user_id'],
            reminder_type='stale_high_discount',
            title=f"Товар с большой скидкой не продается: {rev['product_name']}",
            message=f"Скидка {rev['discount_percent']}% уже {days_stale} дней. Цена: {rev['final_price']:.2f} ₽. Предложите клиентам!",
            priority='high'
        )
        
        if reminder_id:
            created_reminders.append(reminder_id)
            cursor.execute('UPDATE product_revisions SET last_sale_reminder = ? WHERE id = ?', (datetime.now(), rev['id']))
    
    # 3. Товары, требующие решения администратора
    cursor.execute('''
        SELECT r.*, u.vk_id
        FROM product_revisions r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.status = 'admin_decision'
          AND r.admin_decision_reminder_sent = 0
          AND date(r.created_at) < date('now', '-1 day')  # Ждет решения больше 1 дня
    ''')
    
    need_admin_decision = cursor.fetchall()
    
    for rev in need_admin_decision:
        reminder_id = create_smart_reminder(
            cursor=cursor,
            revision_id=rev['id'],
            user_id=None,  # Для админа
            reminder_type='admin_decision',
            title=f"Требуется решение по товару: {rev['product_name']}",
            message=f"Товар просрочен {abs(rev['days_remaining'])} дней. Требуется решение администратора.",
            priority='urgent'
        )
        
        if reminder_id:
            created_reminders.append(reminder_id)
            cursor.execute('UPDATE product_revisions SET admin_decision_reminder_sent = 1 WHERE id = ?', (rev['id'],))
            
            # Уведомление админу в VK
            config = vk_bot.get_config()
            admin_vk_id = config.get('admin_vk_id')
            if admin_vk_id:
                vk_bot.send_message(
                    peer_id=admin_vk_id,
                    message=f"⚠️ *Требуется решение администратора*\n\n📦 {rev['product_name']}\n⏰ Просрочено {abs(rev['days_remaining'])} дней\n👤 Сотрудник: {rev['full_name']}"
                )
    
    # 4. Персональные напоминания для продавцов об их товарах
    cursor.execute('''
        SELECT 
            r.user_id,
            u.full_name,
            u.vk_id,
            COUNT(*) as total_items,
            SUM(CASE WHEN r.days_remaining BETWEEN 0 AND 7 THEN 1 ELSE 0 END) as expiring_soon_count,
            SUM(CASE WHEN r.discount_percent >= 40 THEN 1 ELSE 0 END) as high_discount_count
        FROM product_revisions r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.status = 'active'
          AND (r.last_personal_reminder IS NULL OR date(r.last_personal_reminder) < date('now', '-3 days'))
        GROUP BY r.user_id, u.full_name, u.vk_id
        HAVING COUNT(*) > 0
    ''')
    
    seller_stats = cursor.fetchall()
    
    for seller in seller_stats:
        if seller['expiring_soon_count'] > 0 or seller['high_discount_count'] > 0:
            message = f"👋 {seller['full_name']}, у вас на ревизии:\n"
            if seller['expiring_soon_count'] > 0:
                message += f"📅 {seller['expiring_soon_count']} товар(ов) скоро истекает\n"
            if seller['high_discount_count'] > 0:
                message += f"🏷️ {seller['high_discount_count']} товар(ов) со скидкой 40%+\n"
            message += "\nПроверьте и предложите клиентам!"
            
            reminder_id = create_smart_reminder(
                cursor=cursor,
                revision_id=None,
                user_id=seller['user_id'],
                reminder_type='personal_summary',
                title=f"Ваши товары на ревизии",
                message=message,
                priority='low'
            )
            
            if reminder_id:
                created_reminders.append(reminder_id)
                
                # Обновляем дату последнего напоминания для всех товаров этого пользователя
                cursor.execute('''
                    UPDATE product_revisions 
                    SET last_personal_reminder = ?
                    WHERE user_id = ? AND status = 'active'
                ''', (datetime.now(), seller['user_id']))
                
                # Отправляем в VK если есть ID
                if seller['vk_id']:
                    send_vk_reminder(
                        user_vk_id=seller['vk_id'],
                        title="Ваши товары на ревизии",
                        message=message
                    )
    
    db.commit()
    db.close()
    
    logger.info(f"Smart reminders created: {len(created_reminders)} reminders")
    return created_reminders

def create_smart_reminder(cursor, revision_id, user_id, reminder_type, title, message, priority='medium'):
    """
    Создать умное напоминание в базе данных
    """
    try:
        cursor.execute('''
            INSERT INTO smart_reminders 
            (revision_id, user_id, reminder_type, title, message, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (
            revision_id,
            user_id,
            reminder_type,
            title,
            message,
            priority,
            datetime.now()
        ))
        
        reminder_id = cursor.lastrowid
        logger.info(f"Smart reminder created: id={reminder_id}, type={reminder_type}, user={user_id}")
        return reminder_id
    except Exception as e:
        logger.error(f"Failed to create smart reminder: {e}")
        return None

def send_vk_reminder(user_vk_id, title, message):
    """
    Отправить напоминание в VK
    """
    if not user_vk_id:
        return
    
    try:
        full_message = f"🔔 *{title}*\n\n{message}\n\n📱 Откройте раздел «Ревизия» для подробностей."
        vk_bot.send_message(peer_id=user_vk_id, message=full_message)
        logger.info(f"VK reminder sent to {user_vk_id}: {title}")
    except Exception as e:
        logger.error(f"Failed to send VK reminder: {e}")

def get_smart_reminders(user_id=None, status='pending', limit=50):
    """
    Получить умные напоминания
    """
    db = get_db_connection()
    cursor = db.cursor()
    
    conditions = []
    params = []
    
    if user_id:
        conditions.append("(r.user_id = ? OR r.user_id IS NULL)")
        params.append(user_id)
    
    if status:
        conditions.append("r.status = ?")
        params.append(status)
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    cursor.execute(f'''
        SELECT r.*, 
               p.product_name,
               p.expiry_date,
               p.days_remaining,
               p.discount_percent,
               p.final_price
        FROM smart_reminders r
        LEFT JOIN product_revisions p ON r.revision_id = p.id
        {where_clause}
        ORDER BY 
            CASE priority 
                WHEN 'urgent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END,
            created_at DESC
        LIMIT ?
    ''', params + [limit])
    
    reminders = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return reminders

def mark_reminder_completed(reminder_id, user_id):
    """
    Отметить напоминание как выполненное
    """
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        UPDATE smart_reminders 
        SET status = 'completed', completed_at = ?, completed_by = ?
        WHERE id = ? AND status = 'pending'
    ''', (datetime.now(), user_id, reminder_id))
    
    db.commit()
    affected = cursor.rowcount
    db.close()
    
    if affected > 0:
        logger.info(f"Reminder {reminder_id} marked as completed by user {user_id}")
        return True
    
    return False

def generate_smart_report(period_days=7):
    """
    Сгенерировать умный отчет за период
    """
    stats = get_smart_stats(period_days=period_days)
    
    report = {
        'period': f"Последние {period_days} дней",
        'summary': {
            'total_operations': stats['general'].get('total_operations', 0),
            'total_revenue': stats['general'].get('total_revenue', 0),
            'total_write_off_value': stats['general'].get('total_write_off_value', 0),
            'sales_efficiency': stats['efficiency']['sales_efficiency_percent']
        },
        'top_performers': stats['top_employees'][:3] if stats['top_employees'] else [],
        'top_products': stats['top_products'][:5] if stats['top_products'] else [],
        'current_state': stats['current_state'],
        'recommendations': []
    }
    
    # Генерация рекомендаций
    if stats['current_state'].get('expired', 0) > 0:
        report['recommendations'].append({
            'type': 'urgent',
            'title': 'Просроченные товары',
            'message': f"Есть {stats['current_state']['expired']} просроченных товаров. Требуется решение администратора."
        })
    
    if stats['current_state'].get('expiring_soon', 0) > 5:
        report['recommendations'].append({
            'type': 'high',
            'title': 'Много товаров скоро истекает',
            'message': f"{stats['current_state']['expiring_soon']} товаров истекает в течение недели. Усильте продажи."
        })
    
    if stats['efficiency']['sales_efficiency_percent'] < 70:
        report['recommendations'].append({
            'type': 'medium',
            'title': 'Низкая эффективность продаж',
            'message': f"Эффективность продаж {stats['efficiency']['sales_efficiency_percent']}%. Много списаний."
        })
    
    return report

# ============================================================================
# Flask маршруты
# ============================================================================

@smart_bp.route('/stats', methods=['GET'])
def route_get_smart_stats():
    """Получить умную статистику"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    period = request.args.get('period', '30')
    user_id = request.args.get('user_id')
    
    try:
        period_days = int(period) if period != 'all' else None
        stats = get_smart_stats(user_id=user_id, period_days=period_days)
        return jsonify({'status': 'success', 'stats': stats})
    except Exception as e:
        logger.error(f"Error getting smart stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@smart_bp.route('/reminders', methods=['GET'])
def route_get_smart_reminders():
    """Получить умные напоминания"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    user_id = session['user_id']
    status = request.args.get('status', 'pending')
    
    try:
        reminders = get_smart_reminders(user_id=user_id, status=status)
        return jsonify({'status': 'success', 'reminders': reminders})
    except Exception as e:
        logger.error(f"Error getting smart reminders: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@smart_bp.route('/reminders/<int:reminder_id>/complete', methods=['POST'])
def route_complete_reminder(reminder_id):
    """Отметить напоминание как выполненное"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    user_id = session['user_id']
    
    try:
        success = mark_reminder_completed(reminder_id, user_id)
        if success:
            return jsonify({'status': 'success', 'message': 'Напоминание отмечено как выполненное'})
        else:
            return jsonify({'status': 'error', 'message': 'Напоминание не найдено или уже выполнено'}), 404
    except Exception as e:
        logger.error(f"Error completing reminder: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@smart_bp.route('/report', methods=['GET'])
def route_get_smart_report():
    """Получить умный отчет"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    period = request.args.get('period', '7')
    
    try:
        period_days = int(period)
        report = generate_smart_report(period_days=period_days)
        return jsonify({'status': 'success', 'report': report})
    except Exception as e:
        logger.error(f"Error generating smart report: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@smart_bp.route('/check-reminders', methods=['POST'])
def route_check_reminders():
    """Запустить проверку умных напоминаний (только админ)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для админа'}), 403
    
    try:
        created = check_smart_reminders()
        return jsonify({
            'status': 'success', 
            'message': f'Создано {len(created)} напоминаний',
            'created_count': len(created)
        })
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@smart_bp.route('/dashboard', methods=['GET'])
def route_get_smart_dashboard():
    """Получить данные для умной панели управления"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    
    user_id = session['user_id']
    role = session.get('role', 'employee')
    
    try:
        # Статистика за 7 дней
        stats_7d = get_smart_stats(user_id=(None if role == 'admin' else user_id), period_days=7)
        
        # Статистика за 30 дней
        stats_30d = get_smart_stats(user_id=(None if role == 'admin' else user_id), period_days=30)
        
        # Активные напоминания
        reminders = get_smart_reminders(
            user_id=(None if role == 'admin' else user_id), 
            status='pending', 
            limit=10
        )
        
        # Текущее состояние
        current_state = stats_7d['current_state']
        
        dashboard = {
            'quick_stats': {
                'active_items': current_state.get('total_active', 0),
                'expiring_soon': current_state.get('expiring_soon', 0),
                'need_decision': current_state.get('need_decision', 0),
                'high_discount': current_state.get('high_discount', 0)
            },
            'performance': {
                '7d_revenue': stats_7d['general'].get('total_revenue', 0),
                '7d_sold': stats_7d['general'].get('total_sold_qty', 0),
                '30d_revenue': stats_30d['general'].get('total_revenue', 0),
                '30d_sold': stats_30d['general'].get('total_sold_qty', 0),
                'efficiency': stats_30d['efficiency']['sales_efficiency_percent']
            },
            'reminders': reminders[:5],
            'top_employees': stats_30d['top_employees'][:3] if role == 'admin' else [],
            'top_products': stats_30d['top_products'][:3]
        }
        
        return jsonify({'status': 'success', 'dashboard': dashboard})
    except Exception as e:
        logger.error(f"Error getting smart dashboard: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# Функции для интеграции с планировщиком
# ============================================================================

def daily_smart_check():
    """
    Ежедневная проверка для планировщика
    """
    logger.info("Starting daily smart check...")
    
    try:
        # 1. Проверяем и создаем умные напоминания
        created_reminders = check_smart_reminders()
        
        # 2. Отправляем ежедневный отчет в чат
        send_daily_report_to_chat()
        
        logger.info(f"Daily smart check completed: {len(created_reminders)} reminders created")
        return {
            'reminders_created': len(created_reminders),
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Daily smart check failed: {e}")
        return {'status': 'error', 'error': str(e)}

def send_daily_report_to_chat():
    """
    Отправить ежедневный отчет в VK чат
    """
    try:
        # Получаем статистику за день
        db = get_db_connection()
        cursor = db.cursor()
        
        today = datetime.now().date().isoformat()
        
        # Операции за сегодня
        cursor.execute('''
            SELECT 
                COUNT(*) as today_operations,
                SUM(CASE WHEN action IN ('sold', 'sold_discount', 'sold_promo') THEN quantity ELSE 0 END) as today_sold,
                SUM(CASE WHEN action IN ('sold', 'sold_discount', 'sold_promo') THEN price * quantity ELSE 0 END) as today_revenue
            FROM revision_transactions 
            WHERE date(created_at) = ?
        ''', (today,))
        
        today_stats = dict(cursor.fetchone())
        
        # Текущее состояние
        cursor.execute('''
            SELECT 
                COUNT(*) as total_active,
                SUM(CASE WHEN days_remaining < 0 THEN 1 ELSE 0 END) as expired,
                SUM(CASE WHEN days_remaining BETWEEN 0 AND 3 THEN 1 ELSE 0 END) as urgent_expiring
            FROM product_revisions
            WHERE status IN ('active', 'admin_decision')
        ''')
        
        current_state = dict(cursor.fetchone())
        
        db.close()
        
        # Формируем сообщение
        msg = "📊 *Ежедневный отчет по ревизии*\n\n"
        
        if today_stats['today_operations'] and today_stats['today_operations'] > 0:
            msg += f"✅ *Сегодня продано:* {today_stats['today_sold'] or 0} шт\n"
            msg += f"💰 *Выручка:* {today_stats['today_revenue'] or 0:.2f} ₽\n\n"
        else:
            msg += "ℹ️ *Сегодня операций не было*\n\n"
        
        msg += f"📦 *Всего на ревизии:* {current_state['total_active'] or 0} товаров\n"
        
        if current_state['expired'] and current_state['expired'] > 0:
            msg += f"🔴 *Просрочено:* {current_state['expired']} (требуют решения)\n"
        
        if current_state['urgent_expiring'] and current_state['urgent_expiring'] > 0:
            msg += f"🟠 *Срочно истекают (≤3 дня):* {current_state['urgent_expiring']}\n"
        
        msg += "\n📱 Проверьте раздел «Ревизия» для подробностей."
        
        # Отправляем в общий чат
        config = vk_bot.get_config()
        chat_peer_id = config.get('chat_peer_id')
        
        if chat_peer_id:
            vk_bot.send_message(peer_id=chat_peer_id, message=msg)
            logger.info("Daily report sent to VK chat")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")
        return False

                       