# -*- coding: utf-8 -*-
"""
com_scanner.py — Модуль чтения штрих-кодов из COM-портов
Использует только COM6, чтобы COM3 был свободен для 1С
"""
import serial
import threading
import time
import json
from datetime import datetime
from web_config import logger

# Конфигурация COM-портов
# ВНИМАНИЕ: COM3 отключён, чтобы не конфликтовать с 1С
# Используем только COM6 для нашей программы
COM_PORTS = {
    # 'scanner_1': {'port': 'COM3', 'baudrate': 9600, 'name': 'Сканер 1'},  # ОТКЛЮЧЁН для 1С
    'scanner_2': {'port': 'COM6', 'baudrate': 9600, 'name': 'Сканер 2 (Основной)'},
}

# Глобальная переменная для хранения последнего штрих-кода
last_barcode = None
last_barcode_time = None
barcode_callbacks = []

# Управление состоянием сканеров
scanners_enabled = False
scanner_threads = {}


def add_barcode_callback(callback):
    """Добавить функцию обратного вызова при сканировании"""
    barcode_callbacks.append(callback)


def notify_barcode_scanned(barcode, scanner_name):
    """Уведомить все callback функции о сканировании"""
    global last_barcode, last_barcode_time
    last_barcode = barcode
    last_barcode_time = datetime.now()
    
    logger.info(f"Штрих-код отсканирован ({scanner_name}): {barcode}")
    
    for callback in barcode_callbacks:
        try:
            callback(barcode, scanner_name)
        except Exception as e:
            logger.error(f"Error in barcode callback: {e}")


def read_com_port(port_config, scanner_name):
    """
    Читать данные из COM-порта в фоновом потоке
    """
    port_name = port_config['port']
    baudrate = port_config['baudrate']

    logger.info(f"[{scanner_name}] Попытка открытия {port_name} (baudrate={baudrate})...")

    try:
        # Открываем порт с расширенными параметрами
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5  # Увеличенный таймаут
        )

        logger.info(f"[{scanner_name}] Порт {port_name} открыт успешно!")

        buffer = ''
        last_scan_time = 0

        while True:
            try:
                if ser.in_waiting > 0:
                    # Читаем данные
                    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')

                    # Добавляем в буфер
                    buffer += data

                    # Проверяем есть ли завершающий символ (обычно \r или \n)
                    if '\r' in buffer or '\n' in buffer:
                        # Очищаем буфер от управляющих символов
                        barcode = buffer.strip().replace('\r', '').replace('\n', '')

                        # Проверяем что это похоже на штрих-код (EAN-13, Code-128 и т.д.)
                        if barcode and len(barcode) >= 8 and barcode.isalnum():
                            # Защита от дублирования (не чаще 0.5 сек)
                            current_time = time.time()
                            if current_time - last_scan_time > 0.5:
                                notify_barcode_scanned(barcode, scanner_name)
                                last_scan_time = current_time
                                logger.info(f"[{scanner_name}] Успешное сканирование: {barcode}")

                        # Очищаем буфер
                        buffer = ''

                # Небольшая пауза чтобы не грузить процессор
                time.sleep(0.1)
            except Exception as read_error:
                logger.error(f"[{scanner_name}] Ошибка чтения: {read_error}")
                time.sleep(1)

    except serial.SerialException as e:
        logger.error(f"[{scanner_name}] Ошибка порта {port_name}: {e}")
        logger.error(f"[{scanner_name}] Возможные причины:")
        logger.error(f"[{scanner_name}] 1. Порт занят другой программой (1С, сканер)")
        logger.error(f"[{scanner_name}] 2. Неверный номер порта")
        logger.error(f"[{scanner_name}] 3. Нет прав доступа")
    except Exception as e:
        logger.error(f"[{scanner_name}] Критическая ошибка: {e}")


def start_com_scanners():
    """
    Запустить чтение из всех COM-портов в фоновых потоках
    """
    logger.info("Запуск COM-сканеров штрих-кодов...")

    for scanner_key, port_config in COM_PORTS.items():
        scanner_name = port_config['name']

        # Создаём и запускаем поток для каждого сканера
        thread = threading.Thread(
            target=read_com_port,
            args=(port_config, scanner_name),
            daemon=True,
            name=f"COMScanner-{scanner_key}"
        )
        thread.start()

        logger.info(f"Поток для {scanner_name} ({port_config['port']}) запущен")

    logger.info("Все COM-сканеры запущены")


def get_last_barcode():
    """Получить последний отсканированный штрих-код"""
    return {
        'barcode': last_barcode,
        'timestamp': last_barcode_time.isoformat() if last_barcode_time else None
    }


def clear_last_barcode():
    """Очистить последний штрих-код"""
    global last_barcode, last_barcode_time
    last_barcode = None
    last_barcode_time = None


def enable_scanners():
    """Включить сканеры"""
    global scanners_enabled
    
    if scanners_enabled:
        logger.warning("Сканеры уже включены")
        return False
    
    scanners_enabled = True
    logger.info("Включение COM-сканеров...")
    start_com_scanners()
    return True


def disable_scanners():
    """Выключить сканеры"""
    global scanners_enabled, scanner_threads
    
    if not scanners_enabled:
        logger.warning("Сканеры уже выключены")
        return False
    
    logger.info("Выключение COM-сканеров...")
    scanners_enabled = False
    
    # Потоки остановятся сами при следующей итерации цикла
    # Просто очищаем ссылки
    scanner_threads.clear()
    
    logger.info("Сканеры выключены")
    return True


def get_scanners_status():
    """Получить статус сканеров"""
    return {
        'enabled': scanners_enabled,
        'active_ports': list(COM_PORTS.values()),
        'last_barcode': get_last_barcode()
    }


# Для тестирования
if __name__ == '__main__':
    def test_callback(barcode, scanner_name):
        print(f"📠 {scanner_name}: {barcode} ({datetime.now().strftime('%H:%M:%S')})")
    
    add_barcode_callback(test_callback)
    
    print("🚀 Запуск COM-сканеров... (Ctrl+C для остановки)")
    start_com_scanners()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка сканеров...")
