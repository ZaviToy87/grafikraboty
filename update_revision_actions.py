# -*- coding: utf-8 -*-
"""
update_revision_actions.py — Добавление типов операций в журнал ревизии
"""
import sqlite3

DB_PATH = 'schedule.db'

# Полный перечень типов операций с товарами
REVISION_ACTIONS = {
    # Продажи
    'sold': {
        'label': '💰 Продажа',
        'category': 'sale',
        'description': 'Товар продан клиенту',
        'color': '#22c55e',
        'bg_color': '#f0fdf4',
        'requires_price': True,
        'requires_quantity': True
    },
    'sold_discount': {
        'label': '🏷️ Продажа со скидкой',
        'category': 'sale',
        'description': 'Товар продан со скидкой (уценка по сроку)',
        'color': '#16a34a',
        'bg_color': '#dcfce7',
        'requires_price': True,
        'requires_quantity': True
    },
    'sold_promo': {
        'label': '🎁 Акционная продажа',
        'category': 'sale',
        'description': 'Продажа по акции/промокоду',
        'color': '#059669',
        'bg_color': '#d1fae5',
        'requires_price': True,
        'requires_quantity': True
    },
    
    # Списание
    'written_off_expired': {
        'label': '🗑️ Списание (просрочка)',
        'category': 'write_off',
        'description': 'Товар списан из-за истечения срока годности',
        'color': '#ef4444',
        'bg_color': '#fef2f2',
        'requires_price': False,
        'requires_quantity': True
    },
    'written_off_damaged': {
        'label': '🗑️ Списание (повреждение)',
        'category': 'write_off',
        'description': 'Товар списан из-за повреждения/брака',
        'color': '#dc2626',
        'bg_color': '#fee2e2',
        'requires_price': False,
        'requires_quantity': True
    },
    'written_off_lost': {
        'label': '🗑️ Списание (утеря)',
        'category': 'write_off',
        'description': 'Товар утерян/не найден при инвентаризации',
        'color': '#b91c1c',
        'bg_color': '#fecaca',
        'requires_price': False,
        'requires_quantity': True
    },
    
    # Личное использование
    'taken_personal': {
        'label': '👤 Забрала себе',
        'category': 'personal',
        'description': 'Сотрудник забрал товар для личного использования',
        'color': '#f59e0b',
        'bg_color': '#fef3c7',
        'requires_price': False,
        'requires_quantity': True
    },
    'taken_gift': {
        'label': '🎁 Забрала в подарок',
        'category': 'personal',
        'description': 'Товар взят как подарок (свой/клиенту)',
        'color': '#d97706',
        'bg_color': '#fde68a',
        'requires_price': False,
        'requires_quantity': True
    },
    'taken_test': {
        'label': '🧪 Взяла на пробу',
        'category': 'personal',
        'description': 'Товар взят для тестирования/пробы',
        'color': '#b45309',
        'bg_color': '#fcd34d',
        'requires_price': False,
        'requires_quantity': True
    },
    
    # Обмен и возврат поставщику
    'returned_supplier': {
        'label': '🔄 Возврат поставщику',
        'category': 'return',
        'description': 'Товар возвращён поставщику (брак/просрочка/обмен)',
        'color': '#3b82f6',
        'bg_color': '#dbeafe',
        'requires_price': False,
        'requires_quantity': True
    },
    'exchanged_supplier': {
        'label': '🔄 Обмен у поставщика',
        'category': 'return',
        'description': 'Товар обменён у поставщика на другой',
        'color': '#2563eb',
        'bg_color': '#bfdbfe',
        'requires_price': False,
        'requires_quantity': True
    },
    'exchanged_customer': {
        'label': '🔄 Обмен клиенту',
        'category': 'return',
        'description': 'Клиент обменял товар на другой',
        'color': '#1d4ed8',
        'bg_color': '#93c5fd',
        'requires_price': False,
        'requires_quantity': True
    },
    
    # Перемещение
    'transferred_store': {
        'label': '📦 Перемещение на склад',
        'category': 'transfer',
        'description': 'Товар перемещён со склада в торговый зал или обратно',
        'color': '#8b5cf6',
        'bg_color': '#ede9fe',
        'requires_price': False,
        'requires_quantity': True
    },
    'transferred_branch': {
        'label': '📦 Перемещение в филиал',
        'category': 'transfer',
        'description': 'Товар перемещён в другой филиал/магазин',
        'color': '#7c3aed',
        'bg_color': '#ddd6fe',
        'requires_price': False,
        'requires_quantity': True
    },
    
    # Утилизация
    'utilized': {
        'label': '♻️ Утилизация',
        'category': 'utilization',
        'description': 'Товар утилизирован (экологичная утилизация)',
        'color': '#6b7280',
        'bg_color': '#f3f4f6',
        'requires_price': False,
        'requires_quantity': True
    },
    'donated': {
        'label': '❤️ Пожертвование',
        'category': 'donation',
        'description': 'Товар передан в благотворительность/приют',
        'color': '#ec4899',
        'bg_color': '#fce7f3',
        'requires_price': False,
        'requires_quantity': True
    },
    
    # Изменение цены
    'price_increased': {
        'label': '📈 Цена повышена',
        'category': 'price_change',
        'description': 'Розничная цена товара повышена',
        'color': '#10b981',
        'bg_color': '#d1fae5',
        'requires_price': True,
        'requires_quantity': False
    },
    'price_decreased': {
        'label': '📉 Цена снижена',
        'category': 'price_change',
        'description': 'Розничная цена товара снижена (уценка)',
        'color': '#f59e0b',
        'bg_color': '#fef3c7',
        'requires_price': True,
        'requires_quantity': False
    },
    
    # Возврат от клиента
    'returned_customer': {
        'label': '↩️ Возврат от клиента',
        'category': 'customer_return',
        'description': 'Клиент вернул товар (брак/не подошёл)',
        'color': '#6366f1',
        'bg_color': '#e0e7ff',
        'requires_price': True,
        'requires_quantity': True
    }
}

def create_actions_table():
    """Создать таблицу с типами операций (для справки)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица справочника действий (необязательно, но полезно для документации)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revision_action_types (
            action_code TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            color TEXT,
            bg_color TEXT,
            requires_price INTEGER DEFAULT 0,
            requires_quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Заполняем справочник
    for code, info in REVISION_ACTIONS.items():
        cursor.execute('''
            INSERT OR REPLACE INTO revision_action_types
            (action_code, label, category, description, color, bg_color, requires_price, requires_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            code,
            info['label'],
            info['category'],
            info['description'],
            info['color'],
            info['bg_color'],
            1 if info['requires_price'] else 0,
            1 if info['requires_quantity'] else 0
        ))
    
    conn.commit()
    
    # Считаем сколько добавили
    cursor.execute('SELECT COUNT(*) FROM revision_action_types')
    count = cursor.fetchone()[0]
    
    print("=" * 70)
    print("📋 СПРАВОЧНИК ТИПОВ ОПЕРАЦИЙ")
    print("=" * 70)
    print(f"✅ Всего типов операций: {count}")
    
    # Группируем по категориям
    categories = {}
    for code, info in REVISION_ACTIONS.items():
        cat = info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((code, info))
    
    print("\n📊 По категориям:")
    category_labels = {
        'sale': '💰 Продажи',
        'write_off': '🗑️ Списание',
        'personal': '👤 Личное использование',
        'return': '🔄 Обмен/Возврат',
        'transfer': '📦 Перемещение',
        'utilization': '♻️ Утилизация',
        'donation': '❤️ Пожертвование',
        'price_change': '💲 Изменение цены',
        'customer_return': '↩️ Возврат от клиента'
    }
    
    for cat, items in categories.items():
        print(f"\n{category_labels.get(cat, cat)}:")
        for code, info in items:
            print(f"  • {info['label']} — {info['description']}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ ГОТОВО")
    print("=" * 70)

if __name__ == '__main__':
    create_actions_table()
