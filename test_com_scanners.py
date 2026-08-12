# -*- coding: utf-8 -*-
"""
Тест COM-сканеров — проверить что сканеры работают
"""
from com_scanner import add_barcode_callback, start_com_scanners
import time
from datetime import datetime

def on_scan(barcode, scanner_name):
    print(f"✅ {scanner_name}: {barcode}  [{datetime.now().strftime('%H:%M:%S')}]")

print("📡 ТЕСТ COM-СКАНЕРОВ")
print("=" * 50)
print("Настройте:")
print("  • COM3 — Сканер 1")
print("  • COM6 — Сканер 2")
print("=" * 50)
print("Сканируйте штрих-коды... (Ctrl+C для выхода)\n")

add_barcode_callback(on_scan)
start_com_scanners()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Тест завершён")
