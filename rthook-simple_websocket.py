# -*- coding: utf-8 -*-
"""
rthook-simple_websocket.py - Runtime hook для simple_websocket
Добавляет simple_websocket в sys.modules до импорта engineio
"""
import sys
import os

# Явно импортируем simple_websocket до того, как engineio попытается это сделать
try:
    import simple_websocket
    import simple_websocket.ws
    import simple_websocket.aiows
    import simple_websocket.asgi
    
    # Убеждаемся, что simple_websocket доступен в sys.modules
    if 'simple_websocket' not in sys.modules:
        sys.modules['simple_websocket'] = simple_websocket
    if 'simple_websocket.ws' not in sys.modules:
        sys.modules['simple_websocket.ws'] = simple_websocket.ws
    if 'simple_websocket.aiows' not in sys.modules:
        sys.modules['simple_websocket.aiows'] = simple_websocket.aiows
    if 'simple_websocket.asgi' not in sys.modules:
        sys.modules['simple_websocket.asgi'] = simple_websocket.asgi
        
    print("[RTHOOK] simple_websocket loaded successfully")
except ImportError as e:
    print(f"[RTHOOK] Failed to load simple_websocket: {e}")
