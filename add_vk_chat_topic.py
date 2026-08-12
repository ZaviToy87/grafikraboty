# -*- coding: utf-8 -*-
"""
Добавление темы VK в чат
"""
import sqlite3

conn = sqlite3.connect('schedule.db')
cursor = conn.cursor()

# Проверяем есть ли тема VK
cursor.execute("SELECT id FROM chat_topics WHERE title = 'VK'")
if cursor.fetchone():
    print("✓ Тема VK уже существует")
else:
    cursor.execute("INSERT INTO chat_topics (title) VALUES ('VK')")
    conn.commit()
    print("✓ Тема VK добавлена")

conn.close()
