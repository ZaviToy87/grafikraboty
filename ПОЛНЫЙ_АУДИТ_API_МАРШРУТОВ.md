# 📋 ПОЛНЫЙ АУДИТ API МАРШРУТОВ — GRAFIKRABOTY

**Дата аудита:** 22.03.2026  
**Провёл:** Qwen Code Assistant

---

## 📊 ОБЩАЯ СТАТИСТИКА

| Категория | Количество |
|-----------|------------|
| **Всего маршрутов в Python** | 73 |
| **Всего API вызовов в JS** | 66+ уникальных |
| **Критических несоответствий** | 27 ❌ |
| **Проблем с методами** | 8 ⚠️ |

---

## ✅ РАБОТАЮЩИЕ МАРШРУТЫ (Python ↔ JS совпадают)

### web_server.py (5 маршрутов)
| URL | Метод | Обработчик | Статус |
|-----|-------|------------|--------|
| `/` | GET | `index()` | ✅ |
| `/dashboard` | GET | `dashboard()` | ✅ |
| `/chat` | GET | `chat_page()` | ✅ |
| `/login` | GET | `login_page()` | ✅ |
| `/favicon.ico` | GET | `favicon()` | ✅ |

### web_auth.py (6 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/login` | GET, POST | `login()` | ✅ |
| `/login/verify-telegram` | POST | `verify_telegram()` | ✅ |
| `/login/verify-vk` | POST | `verify_vk()` | ✅ |
| `/logout` | GET | `logout()` | ✅ |
| `/api/vk/send-code` | POST | `api_vk_send_code()` | ✅ |
| `/api/vk/verify-code` | POST | `api_vk_verify_code()` | ✅ |

### web_api.py (19 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/api/schedule` | GET | `api_get_schedule()` | ✅ |
| `/api/schedule/update` | POST | `api_update_schedule()` | ✅ |
| `/api/tasks` | GET | `api_get_tasks()` | ✅ |
| `/api/reminders` | GET | `api_reminders()` | ✅ |
| `/api/files` | GET | `api_get_files()` | ✅ |
| `/api/files/upload` | POST | `api_upload_file()` | ✅ |
| `/api/files/<id>` | GET, DELETE | `api_get_or_delete_file()` | ✅ |
| `/api/files/<id>/view` | GET | `api_view_file()` | ✅ |
| `/api/files/<id>/download` | GET | `api_download_file()` | ✅ |
| `/api/users` | GET | `api_get_users()` | ✅ |
| `/api/colleagues` | GET | `api_get_colleagues()` | ✅ |
| `/api/colleague-tasks` | GET | `api_get_colleague_tasks()` | ✅ |
| `/chat/topics` | GET, POST | `api_get_chat_topics()`, `api_create_chat_topic()` | ✅ |
| `/chat/topics/<id>` | PUT, DELETE | `api_update_chat_topic()`, `api_delete_chat_topic()` | ✅ |
| `/chat/send` | POST | `api_send_chat_message()` | ✅ |
| `/chat/messages` | GET | `api_get_chat_messages()` | ✅ |
| `/files/<id>` | GET | `api_get_file()` | ✅ |
| `/tunnel-info` | GET | `api_tunnel_info()` | ✅ |
| `/tunnel-status` | GET | `api_tunnel_status()` | ✅ |

### web_chat.py (7 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/api/chat/topics` | GET | `get_chat_topics()` | ✅ |
| `/api/chat/topics` | POST | `create_chat_topic()` | ✅ |
| `/api/chat/messages` | GET | `get_chat_messages()` | ✅ |
| `/api/chat/send` | POST | `send_chat_message()` | ✅ |
| `/api/chat/upload` | POST | `upload_chat_file()` | ✅ |
| `/api/chat/messages/<id>` | PUT | `update_chat_message()` | ✅ |
| `/api/chat/messages/<id>` | DELETE | `delete_chat_message()` | ✅ |

### web_work_journal.py (8 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/api/work-journal` | GET | `get_work_journal()` | ✅ |
| `/api/work-journal/open` | POST | `open_shift()` | ✅ |
| `/api/work-journal/entry` | POST | `add_entry()` | ✅ |
| `/api/work-journal/entries` | GET | `get_entries()` | ✅ |
| `/api/work-journal/close` | POST | `close_shift()` | ✅ |
| `/api/work-journal/<id>/close` | POST | `close_shift_by_id()` | ✅ |
| `/api/work-journal/shift/<id>` | GET | `get_shift_details()` | ✅ |
| `/api/work-journal/shift/<id>` | DELETE | `delete_shift()` | ✅ |

### web_barcodes.py (5 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/api/barcodes` | GET | `get_barcodes()` | ✅ |
| `/api/barcodes/add` | POST | `add_barcode()` | ✅ |
| `/api/barcodes/delete/<id>` | POST | `delete_barcode()` | ✅ |
| `/api/barcodes/export` | GET | `export_barcodes()` | ✅ |
| `/api/barcodes/import` | POST | `import_barcodes()` | ✅ |

### web_converter.py (6 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/converter` | GET | `converter_page()` | ✅ |
| `/converter/files` | GET | `get_converter_files()` | ✅ |
| `/converter/upload` | POST | `upload_price_file()` | ✅ |
| `/converter/analyze` | POST | `analyze_prices()` | ✅ |
| `/converter/generate` | POST | `generate_price_tags()` | ✅ |
| `/converter/print` | POST | `print_price_tags()` | ✅ |

### web_admin.py (5 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/api/audit-log` | GET | `api_get_audit_log()` | ✅ |
| `/api/telegram-seen-users` | GET | `api_get_telegram_seen_users()` | ✅ |
| `/api/salary-summary` | GET | `api_get_salary_summary()` | ✅ |
| `/api/employee-stats` | GET | `api_get_employee_stats()` | ✅ |
| `/api/salary-adjustments` | GET | `api_get_salary_adjustments()` | ✅ |

### web_vk_chat.py (5 маршрутов)
| URL | Методы | Обработчик | Статус |
|-----|--------|------------|--------|
| `/api/vk-chat/vk-sync` | POST | `sync_vk_messages()` | ✅ |
| `/api/vk-chat/vk/send` | POST | `send_to_vk()` | ✅ |
| `/api/vk-chat/vk/create-topic` | POST | `create_vk_topic()` | ✅ |
| `/api/vk-chat/vk/download-attachment` | POST | `download_vk_attachment()` | ✅ |
| `/api/vk-chat/vk/status` | GET | `vk_chat_status()` | ✅ |

---

## ❌ ОТСУТСТВУЮЩИЕ МАРШРУТЫ (JS вызывает, но НЕТ в Python)

### КРИТИЧЕСКИЕ ПРОБЛЕМЫ — 27 маршрутов

| № | URL | Вызов в JS | Файл JS | Проблема |
|---|-----|------------|---------|----------|
| 1 | `/api/users/<id>/password` | `PUT` | app.js:404 | **Маршрут не существует** |
| 2 | `/api/users/<id>` | `DELETE` | app.js:568 | **Маршрут не существует** |
| 3 | `/api/telegram-user-map` | `POST` | app.js:627 | **Маршрут не существует** |
| 4 | `/api/telegram-fetch-members` | `POST` | app.js:648 | **Маршрут не существует** |
| 5 | `/api/weekly-digest` | `GET` | app.js:728 | **Маршрут не существует** |
| 6 | `/api/tasks/<id>` | `PUT` | app.js:1176 | **Маршрут не существует** |
| 7 | `/api/tasks/add` | `POST` | app.js:1189, 1646 | **Маршрут не существует** |
| 8 | `/api/tasks/<id>` | `DELETE` | app.js:1213 | **Маршрут не существует** |
| 9 | `/api/colleague-tasks/<id>/complete` | `PATCH` | app.js:1893 | **Маршрут не существует** |
| 10 | `/api/colleague-tasks/<id>/send-telegram` | `POST` | app.js:1912 | **Маршрут не существует** |
| 11 | `/api/colleague-tasks/<id>/thanks` | `POST` | app.js:1325 | **Маршрут не существует** |
| 12 | `/api/colleague-tasks` | `POST` (создание) | app.js:1609 | **Маршрут не существует** |
| 13 | `/api/work-journal/entry/<id>` | `PUT` | app.js:3331 | **Маршрут не существует** |
| 14 | `/api/work-journal/entry/<id>` | `DELETE` | app.js:3363 | **Маршрут не существует** |
| 15 | `/api/work-journal/export` | `GET` | app.js:2914 | **Маршрут не существует** |
| 16 | `/api/salary-adjustments` | `POST` (создание) | app.js:3547 | **Маршрут не существует** |
| 17 | `/api/salary-adjustments/<id>` | `DELETE` | app.js:3566 | **Маршрут не существует** |
| 18 | `/api/schedule/template` | `POST` | app.js:3640 | **Маршрут не существует** |
| 19 | `/api/system/update` | `POST` | app.js:3701 | **Маршрут не существует** |
| 20 | `/api/converter/open` | `POST` | converter.js:97 | **Маршрут не существует** |
| 21 | `/api/barcodes/<id>` | `PUT/GET` | dashboard.html:1219 | **Маршрут не существует** |
| 22 | `/api/barcodes/import-excel` | `POST` | dashboard.html:1271 | **Маршрут не существует** |
| 23 | `/api/admin/backup` | `GET` | dashboard.html:353 | **Маршрут не существует** |
| 24 | `/api/tunnel-logs` | `GET` | tunnel_monitor.html:400 | **Маршрут не существует** |
| 25 | `/api/port-check` | `GET` | tunnel_monitor.html:372 | **Маршрут не существует** |
| 26 | `/api/health` | `GET` | diagnostic.html:87 | **Маршрут не существует** |
| 27 | `/api/chat/vk-status` | `GET` | chat.html:396 | **Маршрут не существует** |

---

## ⚠️ МАРШРУТЫ С НЕПРАВИЛЬНЫМИ МЕТОДАМИ

| № | Маршрут | Ожидаемый метод | Реальный метод | Проблема |
|---|---------|-----------------|----------------|----------|
| 1 | `/api/colleague-tasks` | **POST** (создание) | Только **GET** | JS создаёт задачи, но маршрут только читает |
| 2 | `/api/salary-adjustments` | **POST**, **DELETE** | Только **GET** | JS создаёт/удаляет, но маршрут только читает |
| 3 | `/api/work-journal/entry` | **PUT**, **DELETE** | Только **POST** | JS редактирует/удаляет записи |
| 4 | `/api/tasks` | **POST**, **PUT**, **DELETE** | Только **GET** | JS управляет задачами, но маршрут только читает |
| 5 | `/api/users` | **POST**, **PUT**, **DELETE** | Только **GET** | JS управляет пользователями |
| 6 | `/api/barcodes` | **PUT** | Только **GET** | JS редактирует штрих-коды |
| 7 | `/api/files/<id>` | **PUT** | **GET**, **DELETE** | Нет редактирования файлов |
| 8 | `/api/chat/topics` | **POST** | Есть **GET**, **POST** | ✅ OK |

---

## 📁 ФАЙЛЫ С МАРШРУТАМИ

### Python файлы с маршрутами:
```
C:\Users\User\Desktop\GrafikRaboty\
├── web_server.py       — 5 маршрутов (основные страницы)
├── web_auth.py         — 6 маршрутов (аутентификация)
├── web_api.py          — 19 маршрутов (основное API)
├── web_chat.py         — 7 маршрутов (чат)
├── web_work_journal.py — 8 маршрутов (рабочий журнал)
├── web_barcodes.py     — 5 маршрутов (штрих-коды)
├── web_converter.py    — 6 маршрутов (конвертер)
├── web_admin.py        — 5 маршрутов (админка)
├── web_vk_chat.py      — 5 маршрутов (VK интеграция)
└── web_config.py       — 0 маршрутов (утилиты)
```

### JavaScript файлы с API вызовами:
```
C:\Users\User\Desktop\GrafikRaboty\static\js\
├── app.js              — 66+ API вызовов
└── converter.js        — 5 API вызовов
```

### HTML шаблоны с API вызовами:
```
C:\Users\User\Desktop\GrafikRaboty\templates\
├── dashboard.html      — 7 API вызовов (barcodes, admin)
├── chat.html           — 4 API вызова
├── tunnel_monitor.html — 3 API вызова
├── mobile_guide.html   — 1 API вызов
├── login_vk.html       — 2 API вызова
└── diagnostic.html     — 1 API вызов
```

---

## 🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ

### Приоритет 1 (Критично):
1. **Добавить CRUD для пользователей**: 
   - `/api/users/<id>/password` (PUT)
   - `/api/users/<id>` (DELETE)
2. **Добавить CRUD для задач**: 
   - `/api/tasks/add` (POST)
   - `/api/tasks/<id>` (PUT, DELETE)
3. **Добавить Telegram интеграцию**: 
   - `/api/telegram-user-map` (POST)
   - `/api/telegram-fetch-members` (POST)
4. **Добавить CRUD для colleague-tasks**: 
   - POST (создание)
   - PATCH (завершение)
   - POST (отправка в Telegram)
   - POST (благодарности)

### Приоритет 2 (Важно):
5. **Добавить CRUD для записей рабочего журнала**: 
   - `/api/work-journal/entry/<id>` (PUT, DELETE)
6. **Добавить CRUD для salary-adjustments**: 
   - POST (создание)
   - DELETE (удаление)
7. **Добавить экспорт work-journal**: 
   - `/api/work-journal/export` (GET)
8. **Добавить шаблон графика**: 
   - `/api/schedule/template` (POST)

### Приоритет 3 (Желательно):
9. **Добавить системные маршруты**: 
   - `/api/system/update` (POST)
   - `/api/weekly-digest` (GET)
   - `/api/health` (GET)
10. **Добавить маршруты для barcodes**: 
    - `/api/barcodes/<id>` (PUT)
    - `/api/barcodes/import-excel` (POST)
11. **Добавить маршруты для tunnel**: 
    - `/api/tunnel-logs` (GET)
    - `/api/port-check` (GET)
12. **Добавить маршруты для converter**: 
    - `/api/converter/open` (POST)
13. **Добавить резервное копирование**: 
    - `/api/admin/backup` (GET)
14. **Добавить VK статус чата**: 
    - `/api/chat/vk-status` (GET)

---

## 📌 ВЫВОДЫ

Проект имеет **значительные несоответствия** между frontend (JS) и backend (Python):

- **27 отсутствующих маршрутов** — JS пытается вызвать API которых не существует
- **8 маршрутов с неправильными методами** — JS использует POST/PUT/DELETE, а Python поддерживает только GET
- **Основные проблемные области**: 
  - Управление пользователями (нет CRUD)
  - Управление задачами (нет CRUD)
  - Управление коллегами (нет CRUD)
  - Рабочий журнал (нет редактирования записей)
  - Зарплаты (нет CRUD для надбавок)
  - Telegram интеграция (нет маршрутов)
  - Системные маршруты (нет обновления, health check)

**Рекомендуется**: Добавить все отсутствующие CRUD маршруты в порядке приоритета указанном выше.

---

## 📝 ПАМЯТКА ДЛЯ АССИСТЕНТА

При работе с этим проектом:
1. **ВСЕГДА проверяй** что API маршрут существует прежде чем писать JS код
2. **Сначала создавай** backend маршрут, потом frontend вызов
3. **Используй этот файл** как справочник при добавлении новых функций
4. **Обновляй этот файл** при добавлении новых маршрутов
