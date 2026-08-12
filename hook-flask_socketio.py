# -*- coding: utf-8 -*-
"""
hook-flask_socketio.py - PyInstaller hook для flask-socketio
Явно добавляем simple_websocket как скрытую зависимость
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('simple_websocket') + [
    'simple_websocket',
    'simple_websocket.ws',
    'simple_websocket.aiows',
    'simple_websocket.asgi',
    'simple_websocket.errors',
    'bidict',
    'bidict._base',
    'bidict._immutable',
    'bidict._common',
    'bidict._orderedbid',
    'websocket',
    'websocket._core',
]
