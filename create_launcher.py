# -*- coding: utf-8 -*-
"""
Создать иконку и EXE-файл для запуска сервера
"""
import os
import struct

def create_ico_from_png(png_path, ico_path):
    """
    Создать простую ICO иконку из PNG файла.
    """
    import struct
    
    # Читаем PNG
    with open(png_path, 'rb') as f:
        png_data = f.read()
    
    # Создаём простую ICO структуру (один размер 256x256)
    # ICO Header
    icon_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type=1 (icon), Count=1
    
    # PNG уже содержит данные изображения, используем их как PNG-компрессию в ICO
    # ICO Directory Entry
    width = 0  # 256
    height = 0  # 256
    colors = 0
    reserved = 0
    planes = 1
    bpp = 32
    image_size = len(png_data)
    image_offset = 6 + 16  # Header + Directory entry
    
    directory_entry = struct.pack('<BBBBHHII', 
        width, height, colors, reserved,
        planes, bpp, image_size, image_offset
    )
    
    # Записываем ICO файл
    with open(ico_path, 'wb') as f:
        f.write(icon_header)
        f.write(directory_entry)
        f.write(png_data)
    
    print(f"ICO создан: {ico_path}")
    return True


if __name__ == '__main__':
    # Пути
    base_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(base_dir, 'static', 'images', 'vetgid-logo.png')
    ico_path = os.path.join(base_dir, 'server_icon.ico')
    
    if os.path.exists(png_path):
        create_ico_from_png(png_path, ico_path)
        print(f"✓ Иконка создана: {ico_path}")
    else:
        print(f"✗ PNG не найден: {png_path}")
