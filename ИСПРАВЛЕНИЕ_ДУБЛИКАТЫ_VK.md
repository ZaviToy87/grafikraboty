# 🛡️ ИСПРАВЛЕНИЕ: ДУБЛИКАТЫ СООБЩЕНИЙ VK

## ❌ ПРОБЛЕМА

**Симптомы:**
- Некоторые сообщения из VK появляются в веб-чате **дважды**
- Особенно заметно при плохом интернете
- Дублируются и текст, и фото

**Причина:**
- VK Long Poll может присылать одно событие **дважды**
- Нет проверки на дубликаты
- Каждое событие создаёт новое сообщение в БД

---

## ✅ РЕШЕНИЕ

### 1. Добавлена колонка `vk_conversation_id`

**Таблица:** `chat_messages`

**Назначение:** Хранение уникального ID сообщения VK для проверки дубликатов

**Формат:** `{from_id}_{conversation_message_id}`

**Пример:** `57596922_12345`

---

### 2. Миграция БД

**Файл:** `add_vk_conversation_id_column.py`

**Что делает:**
1. Добавляет колонку `vk_conversation_id`
2. Создаёт индекс для ускорения проверки
3. Заполняет существующие записи NULL

**Запуск:**
```bash
python add_vk_conversation_id_column.py
```

**Результат:**
```
✅ Колонка добавлена
✅ Индекс создан
✅ Записей обновлено: 65
```

---

### 3. Обновлён `web_vk_chat.py`

**Изменения:**

#### А. Проверка на дубликаты (строки 88-100)

```python
# УНИКАЛЬНЫЙ ID для проверки дубликатов
unique_key = f"{from_id}_{conversation_message_id}"

# ПРОВЕРКА НА ДУБЛИКАТЫ
cursor.execute('''
    SELECT id FROM chat_messages 
    WHERE vk_conversation_id = ? 
    LIMIT 1
''', (unique_key,))

existing = cursor.fetchone()
if existing:
    logger.info(f"VK DUPLICATE DETECTED: {unique_key}")
    return jsonify({'status': 'duplicate'})
```

#### Б. Сохранение unique_key при создании (строки 250-330)

```python
cursor.execute('''
    INSERT INTO chat_messages
    (user_id, username, full_name, message, topic_id, attachment_file_id, created_at, vk_conversation_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', (
    user_id,
    f'vk_user_{from_id}',
    full_name,
    text,
    VK_PERMANENT_TOPIC_ID,
    attachment_ids[0],
    datetime.now(),
    unique_key  # Уникальный ID
))
```

#### В. Подробное логирование

```python
logger.info(f"VK sync received: from_id={from_id}, cid={conversation_message_id}, text='{text[:30]}...'")
logger.info(f"VK unique_key: {unique_key}")
logger.info(f"VK message synced: vk_cid={unique_key}")
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Шаг 1: Запусти миграцию

```bash
python add_vk_conversation_id_column.py
```

---

### Шаг 2: Запусти сервер

```bash
python launcher_with_vk.py
```

---

### Шаг 3: Отправь тестовые сообщения

**В VK чат группы:**
1. Отправь текст "Тест 1"
2. Подожди 5 секунд
3. Отправь текст "Тест 2"
4. Подожди 5 секунд
5. Отправь 3 фото

---

### Шаг 4: Проверь логи

**Команда:**
```bash
type logs\web_server.log | findstr "unique_key"
```

**Ожидаемый результат:**
```
VK unique_key: 57596922_12345
VK message synced: vk_cid=57596922_12345
VK unique_key: 57596922_12346
VK message synced: vk_cid=57596922_12346
```

---

### Шаг 5: Проверь дубликаты

**Команда:**
```bash
type logs\web_server.log | findstr "DUPLICATE"
```

**Ожидаемый результат:**
- Пусто (если дубликатов не было)
- Или: `VK DUPLICATE DETECTED: 57596922_12345` (если VK прислал дважды)

---

### Шаг 6: Проверь веб-чат

**URL:**
```
http://192.168.1.207:8080/chat
```

**Ожидание:**
- ✅ "Тест 1" — 1 раз
- ✅ "Тест 2" — 1 раз
- ✅ 3 фото — 3 сообщения

---

## 📊 ПРИМЕР ЛОГИРОВАНИЯ

### Успешная защита от дубликатов:

```
[11:00:00] VK sync received: from_id=57596922, cid=12345, text='Тест 1'
[11:00:00] VK unique_key: 57596922_12345
[11:00:00] VK message synced: vk_cid=57596922_12345

[11:00:05] VK sync received: from_id=57596922, cid=12346, text='Тест 2'
[11:00:05] VK unique_key: 57596922_12346
[11:00:05] VK message synced: vk_cid=57596922_12346

[11:00:10] VK sync received: from_id=57596922, cid=12347, text=''
[11:00:10] VK unique_key: 57596922_12347
[11:00:10] VK MULTIPLE ATTACHMENTS DETECTED: 3 files
[11:00:10] VK attachment message: vk_cid=57596922_12347
```

### Если VK прислал дубликат:

```
[11:00:00] VK sync received: from_id=57596922, cid=12345
[11:00:00] VK unique_key: 57596922_12345
[11:00:00] VK message synced: vk_cid=57596922_12345

[11:00:01] VK sync received: from_id=57596922, cid=12345  ← ДУБЛИКАТ!
[11:00:01] VK unique_key: 57596922_12345
[11:00:01] VK DUPLICATE DETECTED: 57596922_12345
[11:00:01] Return status: duplicate
```

---

## 🔍 ДИАГНОСТИКА

### Проблема 1: Сообщения всё равно дублируются

**Проверь, запущена ли миграция:**

```bash
python -c "import sqlite3; conn=sqlite3.connect('schedule.db'); print([col[1] for col in conn.execute('PRAGMA table_info(chat_messages)').fetchall()])"
```

**Должно быть:**
```
['id', 'user_id', 'username', 'full_name', 'message', 'created_at', 'topic_id', 'attachment_file_id', 'vk_conversation_id']
```

**Если нет `vk_conversation_id`:**
```bash
python add_vk_conversation_id_column.py
```

---

### Проблема 2: Ошибка "database is locked"

**Причина:** БД заблокирована другим процессом

**Решение:**
1. Останови сервер (Ctrl+C)
2. Запусти миграцию
3. Запусти сервер снова

---

### Проблема 3: Старые сообщения дублируются

**Причина:** Миграция заполнила `vk_conversation_id = NULL`

**Решение:**
- Старые сообщения не проверяются (NULL ≠ NULL)
- Только новые сообщения будут защищены
- Это нормально!

---

## 📁 ИЗМЕНЁННЫЕ ФАЙЛЫ

| Файл | Изменения |
|------|-----------|
| `web_vk_chat.py` | Проверка дубликатов + сохранение unique_key |
| `add_vk_conversation_id_column.py` | Новая миграция БД |
| `schedule.db` | Добавлена колонка `vk_conversation_id` |

---

## 🎯 ИТОГИ

### До исправления:
- ❌ Сообщения дублировались
- ❌ Нет проверки на дубликаты
- ❌ VK Long Poll присылал дважды

### После исправления:
- ✅ **Защита от дубликатов** по unique_key
- ✅ **Проверка в БД** перед созданием
- ✅ **Логирование** для отладки
- ✅ **Миграция** для существующей БД

---

## 🚀 ОБНОВЛЕНИЕ

### Для Python версии:

```bash
# 1. Запусти миграцию
python add_vk_conversation_id_column.py

# 2. Перезапусти сервер
Ctrl+C
python launcher_with_vk.py
```

### Для EXE версии:

```bash
# 1. Пересобери
python build_installer_full.py

# 2. Установи
# Output/GrafikRaboty_Setup_v4.29.exe

# 3. Запусти миграцию
python add_vk_conversation_id_column.py
```

---

## 📞 ПОДДЕРЖКА

Если дубликаты всё равно есть:

1. **Проверь логи:**
   ```bash
   type logs\web_server.log | findstr "DUPLICATE"
   ```

2. **Проверь БД:**
   ```bash
   python -c "import sqlite3; conn=sqlite3.connect('schedule.db'); print(conn.execute('SELECT vk_conversation_id, COUNT(*) FROM chat_messages WHERE vk_conversation_id IS NOT NULL GROUP BY vk_conversation_id HAVING COUNT(*) > 1').fetchall())"
   ```
   
   **Должно быть:** `[]` (пусто)

3. **Проверь индекс:**
   ```bash
   python -c "import sqlite3; conn=sqlite3.connect('schedule.db'); print(conn.execute('SELECT name FROM sqlite_master WHERE type=\"index\" AND name=\"idx_vk_conversation\"').fetchone())"
   ```
   
   **Должно быть:** `('idx_vk_conversation',)`

---

*Версия: 1.0*  
*Дата: 26.03.2026*  
*Сосямба Assistant v4.29*
