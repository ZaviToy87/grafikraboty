# -*- coding: utf-8 -*-
"""
test_com_scanner_debug.py — Диагностика COM-сканеров штрих-кодов
Проверяет все доступные COM-порты и помогает найти сканер
"""
import serial
import serial.tools.list_ports
import time
import sys


def list_all_com_ports():
    """Показать все доступные COM-порты"""
    print("=" * 60)
    print("📡 СПИСОК ВСЕХ COM-ПОРТОВ")
    print("=" * 60)
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("❌ COM-порты не найдены!")
        return []
    
    for i, port in enumerate(ports, 1):
        print(f"\n{i}. {port.device}")
        print(f"   Описание: {port.description}")
        print(f"   Hardware ID: {port.hwid}")
        print(f"   Производитель: {port.manufacturer}")
        print(f"   Статус: {'✅ Доступен' if port.status == 'STATUS_OK' else '⚠️ Занят'}")
    
    print("\n" + "=" * 60)
    return ports


def test_com_port(port_name, baudrate=9600, timeout=5):
    """Протестировать конкретный COM-порт"""
    print(f"\n🔍 Тестирование порта {port_name} (baudrate={baudrate})...")
    print(f"   Нажмите Ctrl+C для остановки\n")
    
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
            dsr_timeout_for_close_all=True
        )
        
        print(f"✅ Порт {port_name} открыт успешно!")
        print(f"   Ожидание сканирования штрих-кода...")
        print(f"   (сканируйте штрих-код прямо сейчас)")
        
        buffer = ''
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    if '\r' in buffer or '\n' in buffer:
                        barcode = buffer.strip().replace('\r', '').replace('\n', '')
                        
                        if barcode and len(barcode) >= 8 and barcode.isalnum():
                            print(f"\n📠 ШТРИХ-КОД ПОЛУЧЕН: {barcode}")
                            print(f"   Длина: {len(barcode)} символов")
                            print(f"   Время: {time.strftime('%H:%M:%S')}")
                            print(f"\n   Продолжайте сканировать или нажмите Ctrl+C...")
                        
                        buffer = ''
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Ошибка чтения: {e}")
                time.sleep(1)
        
        ser.close()
        print(f"\n⏰ Таймаут {timeout} сек истёк")
        
    except serial.SerialException as e:
        print(f"❌ ОШИБКА ПОРТА: {e}")
        print(f"\n   Возможные причины:")
        print(f"   1. Порт занят другой программой (1С, сканер)")
        print(f"   2. Неверный номер порта")
        print(f"   3. Нет прав доступа")
        print(f"   4. Устройство не подключено")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


def find_usb_scanners():
    """Найти USB-сканеры штрих-кодов"""
    print("\n" + "=" * 60)
    print("🔍 ПОИСК USB-СКАНЕРОВ ШТРИХ-КОДОВ")
    print("=" * 60)
    
    ports = serial.tools.list_ports.comports()
    usb_scanners = []
    
    for port in ports:
        # Ищем по описанию (типичные названия сканеров)
        description_lower = port.description.lower()
        if any(keyword in description_lower for keyword in [
            'usb', 'scanner', 'штрих', 'barcode', 'pos', 'virtual'
        ]):
            usb_scanners.append(port)
            print(f"\n✅ Найден потенциальный сканер:")
            print(f"   Порт: {port.device}")
            print(f"   Описание: {port.description}")
            print(f"   Hardware ID: {port.hwid}")
    
    if not usb_scanners:
        print("\n⚠️ Явных USB-сканеров не найдено")
        print("   Возможно, сканер эмулирует клавиатуру (HID режим)")
    
    return usb_scanners


def check_port_availability(port_name):
    """Проверить, свободен ли порт"""
    try:
        ser = serial.Serial(port_name, timeout=0.1)
        ser.close()
        return True
    except serial.SerialException:
        return False


def main():
    print("\n" + "=" * 60)
    print("📡 ДИАГНОСТИКА COM-СКАНЕРОВ ШТРИХ-КОДОВ")
    print("=" * 60)
    
    # Шаг 1: Показать все порты
    all_ports = list_all_com_ports()
    
    if not all_ports:
        print("\n❌ Нет COM-портов. Проверьте подключение сканера.")
        return
    
    # Шаг 2: Найти USB-сканеры
    usb_scanners = find_usb_scanners()
    
    # Шаг 3: Предложить тестирование
    print("\n" + "=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ")
    print("=" * 60)
    
    # Автоматически выбрать первые 3 порта для теста
    ports_to_test = []
    
    # Сначала USB-сканеры
    for scanner in usb_scanners:
        ports_to_test.append(scanner.device)
    
    # Затем первые 3 доступных порта
    for port in all_ports[:3]:
        if port.device not in ports_to_test:
            ports_to_test.append(port.device)
    
    print(f"\nПорты для тестирования: {', '.join(ports_to_test)}")
    print(f"\nТекущие настройки в com_scanner.py:")
    print(f"  COM3 (Сканер 1) - {'✅ Свободен' if check_port_availability('COM3') else '❌ Занят'}")
    print(f"  COM6 (Сканер 2) - {'✅ Свободен' if check_port_availability('COM6') else '❌ Занят'}")
    
    print("\n" + "=" * 60)
    print("ИНСТРУКЦИЯ:")
    print("=" * 60)
    print("1. Если сканер в режиме эмуляции клавиатуры (HID) —")
    print("   он будет работать как обычная клавиатура")
    print("   и не требует COM-порт")
    print()
    print("2. Если сканер в режиме COM-порта —")
    print("   выберите нужный порт из списка выше")
    print()
    print("3. Для теста порта введите номер порта (например COM3)")
    print("   или нажмите Enter для выхода")
    
    while True:
        choice = input("\nВведите порт для теста (или Enter для выхода): ").strip()
        
        if not choice:
            print("\n👋 Выход из диагностики")
            break
        
        # Нормализуем ввод
        if not choice.upper().startswith('COM'):
            choice = f'COM{choice}'
        
        choice = choice.upper()
        
        # Проверяем существует ли порт
        port_exists = any(p.device == choice for p in all_ports)
        
        if not port_exists:
            print(f"❌ Порт {choice} не найден")
            continue
        
        # Тестируем порт
        test_com_port(choice)
        
        again = input("\nПротестировать ещё один порт? (да/нет): ").strip().lower()
        if again not in ['да', 'yes', 'y']:
            break
    
    print("\n" + "=" * 60)
    print("✅ Диагностика завершена")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
