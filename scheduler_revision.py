# -*- coding: utf-8 -*-
"""
scheduler_revision.py — Планировщик задач для ревизии товаров
Запускать раз в день в 9:00
"""
import schedule
import time
import threading
from datetime import datetime
from web_revision import check_daily_expirations, send_weekly_report, send_pre_expiry_alerts
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def job_daily_check():
    """Ежедневная проверка истекающих товаров"""
    logger.info(f"[{datetime.now()}] Running daily expiration check...")
    result = check_daily_expirations()
    logger.info(f"[{datetime.now()}] Daily check complete: {result}")

    # Если есть просроченные — можно отправить дополнительное уведомление
    if result.get('expired', 0) > 0:
        logger.info(f"{result['expired']} products expired - notifications will be sent")


def job_weekly_report():
    """Еженедельный отчёт (понедельник 9:00)"""
    logger.info(f"[{datetime.now()}] Running weekly revision report...")
    count = send_weekly_report()
    logger.info(f"[{datetime.now()}] Weekly report sent, {count} items")


def job_pre_expiry_alerts():
    """Заблаговременные уведомления ДО просрочки (ЭТАП 3)"""
    logger.info(f"[{datetime.now()}] Running pre-expiry alerts check...")
    alerts = send_pre_expiry_alerts()
    total = sum(alerts.values())
    if total > 0:
        logger.info(f"[{datetime.now()}] Pre-expiry alerts sent: {alerts}")
    else:
        logger.info(f"[{datetime.now()}] No pre-expiry alerts needed")


def run_scheduler():
    """Запустить планировщик в фоновом потоке"""
    # Ежедневная проверка в 9:00
    schedule.every().day.at("09:00").do(job_daily_check)

    # Заблаговременные уведомления в 9:05 (через 5 мин после основной проверки)
    schedule.every().day.at("09:05").do(job_pre_expiry_alerts)

    # Еженедельный отчёт в понедельник в 9:10
    schedule.every().monday.at("09:10").do(job_weekly_report)

    logger.info("Revision scheduler started with pre-expiry alerts")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту


def start_scheduler():
    """Запустить планировщик в отдельном потоке"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Revision scheduler thread started")


if __name__ == '__main__':
    # Для тестирования
    logger.info("Starting scheduler for testing...")
    run_scheduler()
