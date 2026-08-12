# -*- coding: utf-8 -*-
"""
Диагностика COM-портов — показывает все доступные COM-порты
"""
import serial.tools.list_ports
import sys

print("=" * 60)
print(" ДИАГНОСТИКА COM-ПОРТОВ")
print("=" * 60)

ports = serial.tools.list_ports.comports()

if not ports:
    print("\n❌ COM-порты не найдены!")
    print("   Проверьте подключение сканера")
    sys.exit(1)

print(f"\n📡 Найдено {len(ports)} COM-порт(ов):\n")

for port in ports:
    print(f"✅ {port.device}")
    print(f"   Описание: {port.description}")
    print(f"   Hardware ID: {port.hwid}")
    print(f"   Производитель: {port.manufacturer or 'Неизвестно'}")
    print(f"   VID:PID = {port.vid}:{port.pid}" if port.vid else "")
    print()

print("=" * 60)
print(" РЕКОМЕНДАЦИИ:")
print("=" * 60)
print("""
1. Если сканер подключён но порт занят:
   - Закройте 1С и другие программы использующие COM-порты
   - Проверьте диспетчер устройств Windows

2. Если порт не определяется:
   - Переподключите сканер в другой USB порт
   - Установите драйверы для сканера

3. Для изменения порта в com_scanner.py:
   - Измените COM_PORTS['scanner_2']['port'] на нужный
""")

input("\nНажмите Enter для выхода...")
