#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_sqlite_to_postgres.py
Миграция данных из SQLite в PostgreSQL для Docker развертывания
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
import json
from datetime import datetime

# Конфигурация
SQLITE_DB = 'schedule.db'
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'grafikraboty'),
    'user': os.getenv('POSTGRES_USER', 'grafik'),
    'password': os.getenv('POSTGRES_PASSWORD', 'grafik_secret_2026')
}

# Таблицы для миграции
TABLES = [
    'users',
    'tasks',
    'work_schedule',
    'work_sessions',
    'work_journal_entries',
    'chat_messages',
    'chat_topics',
    'files',
    'barcodes',
    'audit_log',
    'colleague_tasks',
    'salary_adjustments',
    'vk_attachments'
]

# SQL схемы для PostgreSQL
SCHEMAS = {
    'users': """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) DEFAULT 'employee',
            telegram_id VARCHAR(100),
            vk_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'tasks': """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(500) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            due_date TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'work_schedule': """
        CREATE TABLE IF NOT EXISTS work_schedule (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            shift_date DATE NOT NULL,
            shift_type VARCHAR(50),
            start_time TIME,
            end_time TIME,
            is_planned BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, shift_date)
        )
    """,
    'work_sessions': """
        CREATE TABLE IF NOT EXISTS work_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            opening_sum DECIMAL(10, 2) DEFAULT 0,
            closing_sum DECIMAL(10, 2),
            revenue_total DECIMAL(10, 2) DEFAULT 0,
            cash_revenue DECIMAL(10, 2) DEFAULT 0,
            cashless_revenue DECIMAL(10, 2) DEFAULT 0,
            acquiring_amount DECIMAL(10, 2) DEFAULT 0,
            terminal_actual DECIMAL(10, 2) DEFAULT 0,
            operations_in DECIMAL(10, 2) DEFAULT 0,
            operations_out DECIMAL(10, 2) DEFAULT 0,
            discrepancy DECIMAL(10, 2) DEFAULT 0,
            status VARCHAR(50) DEFAULT 'open',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'work_journal_entries': """
        CREATE TABLE IF NOT EXISTS work_journal_entries (
            id SERIAL PRIMARY KEY,
            shift_id INTEGER REFERENCES work_sessions(id) ON DELETE CASCADE,
            entry_type VARCHAR(50),
            amount DECIMAL(10, 2) DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'chat_messages': """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER,
            user_id INTEGER REFERENCES users(id),
            message_text TEXT,
            message_type VARCHAR(50) DEFAULT 'text',
            file_id INTEGER,
            vk_message_id VARCHAR(100),
            vk_synced BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT false
        )
    """,
    'chat_topics': """
        CREATE TABLE IF NOT EXISTS chat_topics (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        )
    """,
    'files': """
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(500) NOT NULL,
            original_filename VARCHAR(500),
            file_path VARCHAR(1000),
            file_size INTEGER,
            file_type VARCHAR(100),
            uploaded_by INTEGER REFERENCES users(id),
            description TEXT,
            category VARCHAR(100),
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'barcodes': """
        CREATE TABLE IF NOT EXISTS barcodes (
            id SERIAL PRIMARY KEY,
            barcode VARCHAR(100) UNIQUE NOT NULL,
            product_name VARCHAR(500) NOT NULL,
            price DECIMAL(10, 2),
            unit VARCHAR(50),
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'audit_log': """
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            action VARCHAR(255) NOT NULL,
            details TEXT,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'colleague_tasks': """
        CREATE TABLE IF NOT EXISTS colleague_tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            created_by INTEGER REFERENCES users(id),
            assigned_to INTEGER REFERENCES users(id),
            thanks_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """,
    'salary_adjustments': """
        CREATE TABLE IF NOT EXISTS salary_adjustments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            amount DECIMAL(10, 2) NOT NULL,
            reason VARCHAR(500),
            adjustment_type VARCHAR(50) DEFAULT 'bonus',
            period DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER REFERENCES users(id)
        )
    """,
    'vk_attachments': """
        CREATE TABLE IF NOT EXISTS vk_attachments (
            id SERIAL PRIMARY KEY,
            message_id INTEGER REFERENCES chat_messages(id) ON DELETE CASCADE,
            attachment_type VARCHAR(50),
            attachment_url VARCHAR(1000),
            attachment_id VARCHAR(255),
            owner_id VARCHAR(100),
            access_key VARCHAR(100),
            file_size INTEGER,
            width INTEGER,
            height INTEGER,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
}


def get_sqlite_connection():
    """Подключение к SQLite"""
    if not os.path.exists(SQLITE_DB):
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_DB}")
    return sqlite3.connect(SQLITE_DB)


def get_postgres_connection():
    """Подключение к PostgreSQL"""
    return psycopg2.connect(**POSTGRES_CONFIG)


def migrate_table(cursor_sqlite, cursor_pg, table_name):
    """Миграция одной таблицы"""
    print(f"  Миграция таблицы: {table_name}")
    
    # Получаем данные из SQLite
    cursor_sqlite.execute(f"SELECT * FROM {table_name}")
    rows = cursor_sqlite.fetchall()
    
    if not rows:
        print(f"    ⚠️ Таблица пуста")
        return 0
    
    # Получаем названия колонок
    columns = [description[0] for description in cursor_sqlite.description]
    
    # Формируем INSERT запрос
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    insert_query = f"""
        INSERT INTO {table_name} ({columns_str}) 
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
    """
    
    # Вставляем данные батчами
    execute_batch(cursor_pg, insert_query, rows, page_size=100)
    
    print(f"    ✅ Мигрировано {len(rows)} записей")
    return len(rows)


def main():
    """Основная функция миграции"""
    print("=" * 60)
    print("🔄 МИГРАЦИЯ SQLite → PostgreSQL")
    print("=" * 60)
    print(f"\n📁 SQLite: {SQLITE_DB}")
    print(f"🗄️  PostgreSQL: {POSTGRES_CONFIG['database']}@{POSTGRES_CONFIG['host']}")
    print()
    
    try:
        # Подключения
        conn_sqlite = get_sqlite_connection()
        conn_pg = get_postgres_connection()
        
        cursor_sqlite = conn_sqlite.cursor()
        cursor_pg = conn_pg.cursor()
        
        # Создание схем
        print("📋 Создание схем таблиц...")
        for table_name, schema in SCHEMAS.items():
            print(f"  Создание таблицы: {table_name}")
            cursor_pg.execute(schema)
        
        conn_pg.commit()
        print("✅ Схемы созданы\n")
        
        # Миграция данных
        print("📊 Миграция данных...")
        total_records = 0
        
        for table_name in TABLES:
            try:
                records = migrate_table(cursor_sqlite, cursor_pg, table_name)
                total_records += records
            except Exception as e:
                print(f"  ❌ Ошибка миграции {table_name}: {e}")
        
        conn_pg.commit()
        
        print()
        print("=" * 60)
        print(f"✅ МИГРАЦИЯ ЗАВЕРШЕНА")
        print(f"📊 Всего мигрировано записей: {total_records}")
        print("=" * 60)
        
        # Закрываем подключения
        cursor_sqlite.close()
        cursor_pg.close()
        conn_sqlite.close()
        conn_pg.close()
        
    except FileNotFoundError as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("Убедитесь что schedule.db существует в текущей директории")
        return 1
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
