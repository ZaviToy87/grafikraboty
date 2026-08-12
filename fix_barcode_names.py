# -*- coding: utf-8 -*-
"""
Скрипт для исправления расхождений в названиях штрих-кодов
"""
import sqlite3

DB_PATH = 'schedule.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Список штрих-кодов для исправления
    fixes = [
        ('4670064652338', 'Альфа пет для средних пород чувствительное пищеварение Баранина потрошки'),
        ('4602009605543', 'Сириус для взр. собак говядина с овощами'),
        ('4602009945526', 'Сириус корм  для взрослых собак крупных пород индейка овощи'),
        ('38100119339', 'Форти флора кошки'),
    ]
    
    print("🔧 Исправляем названия штрих-кодов...")
    
    for factory_barcode, correct_name in fixes:
        cursor.execute('''
            UPDATE barcodes 
            SET product_name = ?
            WHERE factory_barcode = ?
        ''', (correct_name, factory_barcode))
        
        if cursor.rowcount > 0:
            print(f"  ✅ Исправлен: {factory_barcode}")
        else:
            print(f"  ⚠️  Не найден: {factory_barcode}")
    
    conn.commit()
    
    # Проверяем результат
    cursor.execute('SELECT factory_barcode, product_name FROM barcodes WHERE factory_barcode IN (?, ?, ?, ?)', 
                   ['4670064652338', '4602009605543', '4602009945526', '38100119339'])
    
    print("\n📋 Результат:")
    for row in cursor.fetchall():
        print(f"  {row['factory_barcode']}: {row['product_name']}")
    
    conn.close()
    print("\n✅ Готово!")

if __name__ == '__main__':
    main()
