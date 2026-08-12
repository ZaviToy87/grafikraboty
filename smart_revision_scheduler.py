# -*- coding: utf-8 -*-
"""
smart_revision_scheduler.py — Планировщик для умной системы ревизии
"""

import schedule
import time
from datetime import datetime
from web_config import logger
from smart_revision_system import daily_smart_check, send_daily_report_to_chat

def setup_smart_scheduler():
    """
    Настроить расписание для умной системы ревизии
    """
    print("=" * 70)
    print("⏰ НАСТРОЙКА ПЛАНИРОВЩИКА УМНОЙ СИСТЕМЫ РЕВИЗИИ")
    print("=" * 70)
    
    # 1. Ежедневная проверка в 9:00
    schedule.every().day.at("09:00").do(run_daily_smart_check)
    print("✅ Ежедневная проверка: 09:00")
    
    # 2. Ежедневный отчет в чат в 18:00
    schedule.every().day.at("18:00").do(run_daily_report)
    print("✅ Ежедневный отчет в чат: 18:00")
    
    # 3. Еженедельный отчет в понедельник в 10:00
    schedule.every().monday.at("10:00").do(run_weekly_report)
    print("✅ Еженедельный отчет: Понедельник 10:00")
    
    # 4. Проверка каждые 6 часов (для тестирования)
    schedule.every(6).hours.do(run_test_check)
    print("✅ Тестовая проверка: каждые 6 часов")
    
    print("\n" + "=" * 70)
    print("🎯 ПЛАНИРОВЩИК НАСТРОЕН")
    print("=" * 70)
    print("\n📅 Расписание:")
    print("  • 09:00 — Ежедневная проверка напоминаний")
    print("  • 18:00 — Ежедневный отчет в VK чат")
    print("  • Пн 10:00 — Еженедельный отчет")
    print("  • Каждые 6ч — Тестовая проверка")
    
    return schedule

def run_daily_smart_check():
    """
    Запустить ежедневную проверку
    """
    logger.info("🚀 Запуск ежедневной проверки умной системы...")
    try:
        result = daily_smart_check()
        logger.info(f"✅ Ежедневная проверка завершена: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка при ежедневной проверке: {e}")
        return {'status': 'error', 'error': str(e)}

def run_daily_report():
    """
    Запустить отправку ежедневного отчета
    """
    logger.info("📊 Отправка ежедневного отчета в чат...")
    try:
        success = send_daily_report_to_chat()
        if success:
            logger.info("✅ Ежедневный отчет отправлен")
        else:
            logger.warning("⚠️ Не удалось отправить ежедневный отчет")
        return success
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке ежедневного отчета: {e}")
        return False

def run_weekly_report():
    """
    Запустить отправку еженедельного отчета
    """
    logger.info("📈 Отправка еженедельного отчета...")
    try:
        from smart_revision_system import generate_smart_report
        report = generate_smart_report(period_days=7)
        
        # Формируем сообщение для VK
        msg = "📊 *Еженедельный отчет по ревизии*\n\n"
        msg += f"📅 Период: {report['period']}\n"
        msg += f"💰 Выручка: {report['summary']['total_revenue']:.2f} ₽\n"
        msg += f"📦 Продано: {report['summary']['total_operations']} операций\n"
        msg += f"🎯 Эффективность: {report['summary']['sales_efficiency']:.1f}%\n\n"
        
        if report['top_performers']:
            msg += "🏆 *Топ сотрудники:*\n"
            for i, emp in enumerate(report['top_performers'][:3], 1):
                msg += f"{i}. {emp['full_name']} — {emp['revenue']:.2f} ₽\n"
            msg += "\n"
        
        if report['recommendations']:
            msg += "💡 *Рекомендации:*\n"
            for rec in report['recommendations']:
                msg += f"• {rec['message']}\n"
        
        # Отправляем в VK чат
        import vk_bot
        config = vk_bot.get_config()
        chat_peer_id = config.get('chat_peer_id')
        
        if chat_peer_id:
            vk_bot.send_message(peer_id=chat_peer_id, message=msg)
            logger.info("✅ Еженедельный отчет отправлен в VK чат")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке еженедельного отчета: {e}")
        return False

def run_test_check():
    """
    Тестовая проверка (для отладки)
    """
    logger.info("🧪 Запуск тестовой проверки...")
    try:
        # Простая проверка доступности системы
        from smart_revision_system import get_smart_stats
        stats = get_smart_stats(period_days=1)
        logger.info(f"🧪 Тестовая проверка: {stats['general'].get('total_operations', 0)} операций за день")
        return True
    except Exception as e:
        logger.error(f"❌ Тестовая проверка не удалась: {e}")
        return False

def start_scheduler():
    """
    Запустить планировщик в отдельном потоке
    """
    print("=" * 70)
    print("🚀 ЗАПУСК ПЛАНИРОВЩИКА УМНОЙ СИСТЕМЫ")
    print("=" * 70)
    
    # Настраиваем расписание
    schedule = setup_smart_scheduler()
    
    # Запускаем немедленно первую проверку
    print("\n⚡ Запуск первой проверки...")
    run_daily_smart_check()
    
    print("\n🔄 Планировщик запущен. Ожидание задач...")
    print("   (Нажмите Ctrl+C для остановки)")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
    except KeyboardInterrupt:
        print("\n\n🛑 Планировщик остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка в планировщике: {e}")

def manual_check():
    """
    Ручной запуск проверки (для тестирования)
    """
    print("=" * 70)
    print("🔄 РУЧНОЙ ЗАПУСК ПРОВЕРКИ")
    print("=" * 70)
    
    print("1. Проверка умных напоминаний...")
    result = run_daily_smart_check()
    print(f"   Результат: {result}")
    
    print("\n2. Отправка отчета в чат...")
    success = run_daily_report()
    print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    
    print("\n3. Получение статистики...")
    from smart_revision_system import get_smart_stats
    stats = get_smart_stats(period_days=7)
    print(f"   Операций за 7 дней: {stats['general'].get('total_operations', 0)}")
    print(f"   Выручка: {stats['general'].get('total_revenue', 0):.2f} ₽")
    
    print("\n" + "=" * 70)
    print("✅ РУЧНАЯ ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 70)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Умная система ревизии - планировщик')
    parser.add_argument('--manual', action='store_true', help='Ручной запуск проверки')
    parser.add_argument('--start', action='store_true', help='Запустить планировщик')
    parser.add_argument('--test', action='store_true', help='Тестовая проверка')
    
    args = parser.parse_args()
    
    if args.manual:
        manual_check()
    elif args.test:
        run_test_check()
    elif args.start:
        start_scheduler()
    else:
        print("Используйте:")
        print("  python smart_revision_scheduler.py --manual  # Ручная проверка")
        print("  python smart_revision_scheduler.py --start   # Запустить планировщик")
        print("  python smart_revision_scheduler.py --test    # Тестовая проверка")