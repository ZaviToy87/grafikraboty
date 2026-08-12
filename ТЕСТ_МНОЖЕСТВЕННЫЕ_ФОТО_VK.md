# 📸 ТЕСТИРОВАНИЕ МНОЖЕСТВЕННЫХ ФОТО VK

## 🚀 ИНСТРУКЦИЯ ПО ПРОВЕРКЕ

### Шаг 1: Обнови файлы

Файлы уже обновлены! Просто перезапусти сервер.

---

### Шаг 2: Перезапусти сервер

```bash
Ctrl+C
python launcher_with_vk.py
```

---

### Шаг 3: Отправь тестовые фото

**В VK чат группы:**
1. Отправь **3-5 фото одновременно**
2. Можно с текстом "Тест множественные фото"
3. Жди 10-15 секунд

---

### Шаг 4: Проверь логи VK бота

**Команда:**
```bash
type logs\vk_bot.log | findstr "MULTIPLE"
```

**Ожидаемый результат:**
```
VK MULTIPLE ATTACHMENTS: 3 files
  Attachment 1: type=photo
  Attachment 2: type=photo
  Attachment 3: type=photo
```

**Если пусто:**
- VK не присылает вложения
- Или присылает в другом формате

---

### Шаг 5: Проверь логи веб-сервера

**Команда:**
```bash
type logs\web_server.log | findstr "MULTIPLE"
```

**Ожидаемый результат:**
```
VK MULTIPLE ATTACHMENTS DETECTED: 3 files
  Attachment 1: type=photo
  Attachment 2: type=photo
  Attachment 3: type=photo
VK First attachment: {'photo': {...}}
```

**Если пусто:**
- Проблема с передачей данных от vk_bot.py
- Проверь `type logs\vk_bot.log | findstr "синхронизировано"`

---

### Шаг 6: Проверь загрузку фото

**Команда:**
```bash
type logs\web_server.log | findstr "downloaded"
```

**Ожидаемый результат:**
```
VK photo downloaded: vk_photo_57596922_20260326_120001_1234.jpg
VK photo downloaded: vk_photo_57596922_20260326_120002_5678.jpg
VK photo downloaded: vk_photo_57596922_20260326_120003_9012.jpg
```

**Если пусто:**
- Проблема с загрузкой фото из VK
- Проверь `type logs\web_server.log | findstr "attachment"`

---

### Шаг 7: Проверь веб-чат

**URL:**
```
http://192.168.1.207:8080/chat
```

**Действия:**
1. Открой чат
2. Выбери тему "VK" (topic_id=3)
3. **Все 3-5 фото должны быть!**

---

## 🔍 ДИАГНОСТИКА

### Проблема 1: В логах нет "MULTIPLE"

**Возможная причина:**
VK присылает только одно фото или вложения в другом поле

**Решение:**
Проверь полную структуру события:
```bash
type logs\vk_bot.log | findstr "event_data keys"
```

**Должно быть:**
```
VK event_data keys: ['type', 'object', 'message', 'attachments']
```

**Если `attachments` нет в списке:**
- VK API не присылает вложения в этом формате
- Нужно проверять `object.message.attachments`

---

### Проблема 2: Вложения есть, но не загружаются

**Лог:**
```
VK attachment: {'type': 'photo', 'photo': {...}}
```

**Решение:**
Проверь, есть ли URL у фото:
```bash
type logs\web_server.log | findstr "photo_url"
```

**Если нет URL:**
- VK не предоставляет URL фото
- Проблема с VK API

---

### Проблема 3: Фото загружены, но не в чате

**Проверь БД:**
```bash
python test_multiple_photos.py
```

**Результат:**
- Если файлы есть в БД — проблема с отображением (JS)
- Если файлов нет — проблема с записью в БД

---

## 📊 ПОЛНАЯ ОТЛАДКА

### Включи DEBUG логирование:

**1. Отправь фото в VK**

**2. Проверь логи vk_bot.py:**
```bash
type logs\vk_bot.log
```

**Ищи:**
- `VK event_data keys` — структура события
- `VK attachments count` — количество вложений
- `VK MULTIPLE ATTACHMENTS` — множественные фото
- `VK сообщение синхронизировано` — успешная отправка

**3. Проверь логи web_server.log:**
```bash
type logs\web_server.log
```

**Ищи:**
- `VK sync received` — получено сообщение
- `VK MULTIPLE ATTACHMENTS DETECTED` — множественные фото
- `VK photo downloaded` — загрузка фото
- `VK attachment saved to files` — сохранение в БД
- `VK attachment message` — создание сообщения

---

## 🎯 ПРИМЕР УСПЕШНОЙ ЗАГРУЗКИ

**Логи vk_bot.log:**
```
[12:00:00] VK event_data keys: ['type', 'object', 'message']
[12:00:00] VK message keys: ['from_id', 'peer_id', 'text', 'attachments']
[12:00:00] VK attachments count: 3
[12:00:00] VK MULTIPLE ATTACHMENTS: 3 files
  Attachment 1: type=photo
  Attachment 2: type=photo
  Attachment 3: type=photo
[12:00:00] VK First attachment: {'type': 'photo', 'photo': {'sizes': [...]}}
[12:00:00] VK сообщение синхронизировано: {'status': 'ok'}
```

**Логи web_server.log:**
```
[12:00:00] VK sync received: from_id=57596922, cid=12345, text='Тест', attachments=3
[12:00:00] VK event keys: ['type', 'object', 'message']
[12:00:00] VK MULTIPLE ATTACHMENTS DETECTED: 3 files
  Attachment 1: type=photo
  Attachment 2: type=photo
  Attachment 3: type=photo
[12:00:00] VK First attachment: {'type': 'photo', 'photo': {'sizes': [...]}}
[12:00:01] VK photo downloaded: vk_photo_57596922_20260326_120001_1234.jpg
[12:00:02] VK photo downloaded: vk_photo_57596922_20260326_120002_5678.jpg
[12:00:03] VK photo downloaded: vk_photo_57596922_20260326_120003_9012.jpg
[12:00:03] VK attachment message: vk_id=57596922, msg_id=201, attachment=101, vk_cid=57596922_12345
[12:00:03] VK attachment message: vk_id=57596922, msg_id=202, attachment=102, vk_cid=57596922_12345
[12:00:03] VK attachment message: vk_id=57596922, msg_id=203, attachment=103, vk_cid=57596922_12345
```

---

## 📞 ЕСЛИ ВСЁ СЛОМАЛОСЬ

**1. Проверь, запущен ли сервер:**
```bash
curl http://127.0.0.1:8080/login
```

**2. Проверь, запущен ли VK бот:**
```bash
tasklist | findstr "python"
```

**3. Перезапусти сервер:**
```bash
Ctrl+C
python launcher_with_vk.py
```

**4. Отправь фото ещё раз**

**5. Проверь логи:**
```bash
type logs\vk_bot.log | findstr "MULTIPLE"
type logs\web_server.log | findstr "MULTIPLE"
```

---

*Версия: 1.0*  
*Дата: 26.03.2026*  
*Сосямба Assistant v4.29*
