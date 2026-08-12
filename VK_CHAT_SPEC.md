# 📱 VK ЧАТ — ТЕХНИЧЕСКОЕ ЗАДАНИЕ

**Версия:** 1.0  
**Дата:** 22 марта 2026 г.

---

## 🎯 ЦЕЛЬ

Создать аналог Telegram чата с интеграцией ВКонтакте:
- Сообщения отправляются в чат группы VK
- Сотрудники пишут боту → сообщения в чате
- Файлы/фото сохраняются на сервере
- Уведомления о новых сообщениях

---

## 📁 СТРУКТУРА

### 1. **БАЗА ДАННЫХ**

**Новые таблицы:**
```sql
-- VK сообщения
CREATE TABLE vk_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vk_id INTEGER NOT NULL,           -- VK ID отправителя
    user_id INTEGER,                   -- ID пользователя в системе
    message_text TEXT,                 -- Текст сообщения
    has_attachment INTEGER DEFAULT 0,  -- Есть ли вложения
    attachment_type TEXT,              -- photo, document, audio
    attachment_path TEXT,              -- Путь к файлу
    direction TEXT DEFAULT 'incoming', -- incoming/outgoing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- VK вложения
CREATE TABLE vk_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    file_type TEXT,                    -- photo, document, audio, video
    file_path TEXT NOT NULL,
    file_size INTEGER,
    original_name TEXT,
    vk_file_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES vk_messages(id)
);

-- Маппинг VK ID ↔ user_id (расширение)
ALTER TABLE vk_config ADD COLUMN last_message_ts INTEGER;
```

### 2. **МОДУЛИ**

**web_chat.py** — новый файл:
```python
# Функции:
- get_chat_messages(limit=50) — получить сообщения
- send_message_to_vk(text, attachments) — отправить в VK
- save_attachment(file, message_id) — сохранить файл
- process_vk_message(event) — обработка входящих
```

**vk_bot.py** (дополнение):
```python
# Новые функции:
- send_message_to_chat(peer_id, message, attachments)
- get_chat_messages(peer_id, count)
- upload_photo(file_path)
- upload_document(file_path)
```

### 3. **API РОУТЫ**

```python
# web_chat.py

GET /api/chat/messages?topic_id=1&limit=50
POST /api/chat/send (text, files[])
GET /api/chat/attachments/<message_id>
POST /api/chat/upload (multipart/form-data)
GET /api/chat/vk-status (статус подключения VK)
```

### 4. **VK LONG POLL**

**Обработка событий:**
```python
# message_new — новое сообщение
if message.from_id > 0:  # Не от бота
    user_id = vk_id_to_user_id(message.from_id)
    save_message(
        vk_id=message.from_id,
        user_id=user_id,
        text=message.text,
        attachments=message.attachments
    )
    emit('chat_message', data, namespace='/chat')
```

### 5. **ВЕБ-ИНТЕРФЕЙС**

**chat.html:**
```html
<div class="chat-container">
    <div class="chat-messages" id="chat-messages">
        <!-- Сообщения -->
    </div>
    <div class="chat-input">
        <input type="text" id="message-input" placeholder="Сообщение...">
        <button onclick="uploadFile()">📎</button>
        <button onclick="sendMessage()">➤</button>
    </div>
</div>
```

**Socket.IO:**
```javascript
socket.on('chat_message', (data) => {
    appendMessage(data);
    playNotificationSound();
});
```

---

## 🔄 ПОТОК ДАННЫХ

### Входящее сообщение:
```
VK → Long Poll → vk_bot.py → web_chat.py → БД → Socket.IO → Веб-интерфейс
```

### Исходящее сообщение:
```
Веб-интерфейс → Socket.IO → web_chat.py → vk_bot.py → VK API → Чат группы
```

### Загрузка файла:
```
Веб-интерфейс → Upload → web_chat.py → uploads/vk/<date>/<file>
→ vk_bot.py → VK Documents/Photos → Чат
```

---

## 📊 VK API МЕТОДЫ

### Отправка:
- `messages.send` — отправить сообщение
- `messages.getHistory` — получить историю
- `photos.getMessagesUploadServer` — загрузка фото
- `docs.getMessagesUploadServer` — загрузка документов

### Получение:
- Long Poll Server (`groups.getLongPollServer`)
- Обработка событий `message_new`

---

## 🗂️ ПАПКИ

```
uploads/
└── vk/
    ├── 2026-03/
    │   ├── photo_146411666_456789012.jpg
    │   └── document_1234567890.pdf
    └── 2026-04/
        └── ...
```

---

## 🔐 БЕЗОПАСНОСТЬ

1. Проверка `user_id` при отправке
2. Валидация файлов (тип, размер ≤ 50MB)
3. Ограничение частоты (rate limiting)
4. Логирование всех операций

---

## 📈 МЕТРИКИ

- Количество сообщений в день
- Размер загруженных файлов
- Активные пользователи чата
- Время ответа бота

---

**Сосямба спроектировал! Приступаю к реализации! 🚀**
