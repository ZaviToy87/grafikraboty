# КОНСТИТУЦИЯ АССИСТЕНТА ДЛЯ СОСЯМБЫ

## 1. ЛИЧНОСТЬ
- Меня зовут **Сосямба**.
- Обращайся ко мне по имени в начале каждого разговора.
- Говори со мной дружелюбно, но по делу.

## 2. ГЛАВНОЕ ПРАВИЛО: СПРАШИВАТЬ РАЗРЕШЕНИЯ
Ты имеешь **полный доступ** к моему компьютеру, НО должен спрашивать разрешение перед:

### Файловые операции:
- ✅ **Можно без спроса**: читать файлы, показывать содержимое, искать файлы
- ❌ **Спрашивать обязательно**:
  - Изменение/редактирование файлов
  - Удаление любых файлов
  - Переименование или перемещение
  - Создание новых файлов в системных папках

### Команды в терминале:
- ✅ **Можно без спроса**:
  - `dir`, `ls`, `cd`, `pwd`, `type` (просмотр)
  - `git status`, `git log` (только чтение)
  - `python --version`, `node --version`
- ❌ **Спрашивать обязательно**:
  - Любые команды, изменяющие систему
  - Установка/удаление программ
  - Команды с `sudo` или административными правами
  - `rm`, `del`, `format`, `shutdown`

### Сеть:
- ❌ **Спрашивать перед**:
  - Отправкой данных куда-либо
  - Скачиванием файлов
  - Открытием веб-страниц

## 3. ПАМЯТЬ
- Запоминай всё важное из наших разговоров.
- Если я спрашиваю про что-то из прошлого — ищи в истории.
- При каждом запуске напоминай мне, что ты помнишь предыдущие сессии.

## 4. ФОРМАТ ОТВЕТОВ
- Перед опасными действиями всегда пиши: "⚠️ Требуется разрешение: [действие]. Выполнить? (да/нет)"
- Жди моего ответа перед выполнением.
- Если я отвечаю "да" или "+" — выполняй.
- Если "нет", "-" или молчание — не выполняй.

## Qwen Added Memories
### 📋 ОСНОВНАЯ ИНФОРМАЦИЯ
- Пользователя зовут **Денис**
- Денис из **Тольятти**
- Telegram Дениса: **@denisvetgid**, ID: **701768868**
- Telegram API: **8755572729:AAGAvyRp6Uni_wCbwjGIe2WRLOPUSlQ3iAc**
- Денис хранит все проекты в папке **F:\Обучение**

### 🤖 SOSYAMBA ASSISTANT v4.0
**Основной проект:** C:\Users\User\Desktop\GrafikRaboty

**Компоненты:**
1. **Telegram-бот** @ZaviToy_Assist_bot (доступ только для ID 701768868)
2. **Веб-интерфейс** localhost:8080
3. **База данных** schedule.db (SQLite)
4. **VK верификация** admin_vk_id=146411666
5. **Повторяющиеся задачи** recurring_schedule.py
6. **Sales модуль** для анализа продаж
7. **MCP система** GrafikRaboty (порт 8081)

**Структура файлов:**
- web_server.py - главный сервер (Flask + Socket.IO)
- web_api.py - API маршруты (график, задачи, файлы, чат)
- web_auth.py - аутентификация (Telegram, VK верификация)
- web_chat.py - чат API
- web_work_journal.py - рабочий журнал
- web_barcodes.py - штрихкоды
- web_converter.py - конвертер ценников
- web_admin.py - админ панель
- web_vk_chat.py - VK интеграция
- vk_bot.py - VK бот (отправка сообщений, long polling)
- vk_config.json - VK конфигурация (token, group_id=199112265, chat_peer_id=2000000001)
- telegram_config.json - Telegram конфигурация
- schedule.db - SQLite база данных (12 таблиц)

**Базы данных (12 таблиц):**
users, tasks, schedule, files, audit_log, chat_messages, chat_topics, work_journal_shift, work_journal_entries, salary_adjustments, barcodes, colleague_tasks

### 🤖 MCP СИСТЕМА (Multi-agent Cooperative Protocol)

**Путь:** C:\Users\User\Desktop\GrafikRaboty\.mcp\
**Порт:** 8081
**Запуск:** python .mcp\mcp_server.py или Start_MCP_Server.bat

**Агенты (9):**
1. ✅ **code_fixer** (565 строк) - Исправление кода с бэкапами - ТЕСТИРОВАНО
2. ✅ **server_controller** (467 строк) - Мониторинг сервера - ТЕСТИРОВАНО
3. ✅ **api_tester** (140 строк) - Тестирование API (12 эндпоинтов) - ТЕСТИРОВАНО
4. ✅ **ui_verifier** (160 строк) - Проверка UI - СОЗДАН
5. ✅ **security_auditor** (220 строк) - Аудит безопасности - ТЕСТИРОВАНО
6. ✅ **desktop_automation** (729 строк) - Автоматизация рабочего стола - СОЗДАН
7. ✅ **code_analyzer** - Статический анализ кода - ТЕСТИРОВАНО
8. ⚠️ **vk_sync_monitor** - Только конфиг
9. ⚠️ **integration_tester** - Только конфиг

**API ENDPOINTS (порт 8081):**
- GET /api/health - статус MCP
- GET /api/status - общая информация
- GET /api/agents - список агентов
- GET /api/agents/{id}/config - конфиг агента
- GET /api/agents/{id}/results/latest - результаты
- POST /api/agents/{id}/execute - запуск агента

**Файлы MCP:**
- .mcp/mcp_server.py (416 строк) - HTTP сервер
- .mcp/config.json - Конфигурация 8 агентов
- .mcp/USER_GUIDE.md - Инструкция для ИИ
- .mcp/AGENTS_STATUS.md - Статус агентов
- .mcp/backups/ - Резервные копии
- logs/mcp*.log - Логи агентов

**Зависимости:**
pip install psutil requests jinja2 selenium pyautogui opencv-python numpy

### 📊 ИСПРАВЛЕННЫЕ МАРШРУТЫ API (27 отсутствующих + 8 с неправильными методами)

✅ /api/tasks POST, PUT, DELETE - CRUD задач
✅ /api/users POST, PUT, DELETE, /api/users/<id>/password PUT - CRUD пользователей
✅ /api/telegram-user-map POST, /api/telegram-fetch-members POST - Telegram интеграция
✅ /api/colleague-tasks POST, PATCH, /<id>/thanks POST, /<id>/send-telegram POST - задачи коллег
✅ /api/work-journal/entry/<id> PUT, DELETE, /export GET - рабочий журнал CRUD
✅ /api/salary-adjustments POST, DELETE - корректировки зарплаты
✅ /api/schedule/template POST - шаблон графика
✅ /api/system/update POST, /api/health GET - системные
✅ /api/barcodes/<id> GET/PUT, /import-excel POST - штрихкоды CRUD
✅ /api/admin/backup GET - бэкап БД
✅ /api/tunnel-logs GET, /api/port-check GET - туннель
✅ /api/chat/vk-status GET - VK статус
✅ /api/converter/open POST - конвертер
✅ /api/files/<id>/download GET - скачивание файлов (исправлено с JSON на файл)

### 🐛 ИСПРАВЛЕННЫЕ ПРОБЛЕМЫ

1. **Скачивание файлов** - изменён JS с /api/files/<id> на /api/files/<id>/download
2. **VK сообщения** - переписана отправка через urllib напрямую с детальным логированием
3. **Целостность БД** - 13 записей work_journal_entries удалены (несуществующие shift_id)
4. **Work Journal** - исправлено определение закрытых смен (closing_count вместо closed_at)
5. **Английские логи** - исправлены в VK модуле

### 📝 ИСТОРИЯ ИЗМЕНЕНИЙ

**v4.5 (22.03.2026):**
- MCP Code Analyzer нашёл 110 проблем (29 high, 51 medium, 30 low)
- MCP API Tester проверил 12 эндпоинтов (1 passed, 11 failed из-за авторизации)
- MCP Security Auditor: 0 проблем безопасности
- Создан полный отчёт: ПОЛНЫЙ_АНАЛИЗ_ПРОЕКТА_22.03.2026.md

**v4.4:**
- Исправлены проблемы Work Journal (closing_count, кнопка удаления)
- Изменены файлы: static/js/app.js (строка 2773), web_work_journal.py (строка 75)

**v4.3:**
- Добавлены недостающие API маршруты
- Исправлено скачивание файлов
- Улучшена VK верификация

**v4.2:**
- Восстановлена целостность БД
- Добавлен MCP Code Analyzer

### 🔧 ГОРЯЧИЕ КЛАВИШИ И БЫСТРЫЙ ДОСТУП

**Команды бота:**
- /search /read /write /backup (файлы)
- /status /cpu /disk /processes (система)
- /task /tasks /reminder (задачи)
- /exec (команды)
- /help (справка)

**MCP команды:**
- mcp.server.control
- mcp.ui.verify
- mcp.api.test
- mcp.security.audit
- mcp.code.fix
- mcp.status

**Быстрый доступ к API:**
```bash
curl http://localhost:8081/api/status
curl -X POST http://localhost:8081/api/agents/code_analyzer/execute
curl http://localhost:8081/api/agents/code_analyzer/results/latest
```

### 📂 ПУТИ К ФАЙЛАМ

**Проект GrafikRaboty:**
- Главный: C:\Users\User\Desktop\GrafikRaboty\
- MCP: C:\Users\User\Desktop\GrafikRaboty\.mcp\
- Логи MCP: C:\Users\User\Desktop\GrafikRaboty\logs\mcp*.log
- Бэкапы MCP: C:\Users\User\Desktop\GrafikRaboty\.mcp\backups\

**Универсальный ассистент:**
- Папка: C:\Users\User\Desktop\universal_assistant_bot\
- Главный файл: C:\Users\User\Desktop\ЗАПУСТИТЬ_ASSISTANT.bat
- Основной код: C:\Users\User\Desktop\universal_assistant_bot\assistant_v3.py
- Данные: C:\Users\User\Desktop\universal_assistant_bot\assistant_data\
- AI мосты: C:\Users\User\Desktop\universal_assistant_bot\ai_bridge\

**Qwen:**
- CLI путь: C:\Users\User\AppData\Roaming\npm\qwen.cmd
- Память: C:\Users\User\.qwen\QWEN.md
- Временные файлы: C:\Users\User\.qwen\tmp\

### 🎯 ТЕКУЩИЕ ЗАДАЧИ И ПРОБЛЕМЫ

**На 22.03.2026:**
1. 🔴 Рефакторинг web_api.py (7 сложных функций)
2. 🔴 Рефакторинг web_work_journal.py (2 сложные функции)
3. 🔴 Рефакторинг web_auth.py (login - 112 строк, сложность 17)
4. 🟠 Рефакторинг fix_db_integrity.py (215 строк, сложность 29)
5. 🟠 Рефакторинг sales/analyzer/parser.py (сложность 29)
6. 🟡 Добавить docstring для 30 функций

**Статус MCP агентов:**
- 5 работают и тестированы
- 2 только конфиги (vk_sync_monitor, integration_tester)
- 2 в разработке

### 💾 ЛОГИРОВАНИЕ

**Денис хочет полное логирование:**
- Сохранять ВСЮ переписку полностью без сокращений
- У него много места на диске
- Записывать: задачи, проблемы, решения, код, настройки, файлы, пути, токены, ID, команды
- Всё подряд без фильтрации

---

*Последнее обновление: 22.03.2026 21:27*
*Версия памяти: 4.5*
*Сосямба Assistant*
- Исправления админ-панели v4.6 (22.03.2026): Добавлены API /api/salary-summary, /api/employee-stats, /api/system/update, /api/vk-chat/vk-seen-users, /api/vk-chat/vk-user-map. Исправлены: loadAuditLog() путь, salary-adjustments использует таблицу salary_adjustments. Удалён дубликат api_system_update. Изменены файлы: web_api.py (+300 строк), web_admin.py (исправлен salary-adjustments), web_vk_chat.py (+100 строк), static/js/app.js (исправлены пути API).
- Синхронизация VK v4.6 (22.03.2026 23:45): Исправлена двусторонняя синхронизация. Веб-чат→VK: web_chat.py отправляет через vk_bot.send_message(). VK→веб-чат: исправлен путь /api/vk-chat/vk-sync, исправлена проверка peer_id>=2000000000. Обработка фото: скачивание, сохранение в uploads/, запись в БД files и chat_messages, отправка через Socket.IO. Изменены файлы: web_chat.py, web_vk_chat.py, vk_bot.py.
- Tunnel Info API fix (23.03.2026 00:00): Исправлен /api/tunnel-info → /tunnel-info (api_bp без префикса). Формат ответа: {status: 'ok', tunnel_url: '', password: ''}. JS: fetch('/tunnel-info'). Файл tunnel_info.json существует.
- ГРАФИК РАБОТЫ v4.9 - ПОЛНАЯ ИНФОРМАЦИЯ:

📁 ПРОЕКТ: C:\Users\User\Desktop\GrafikRaboty

🗄️ БАЗЫ ДАННЫХ (12 таблиц):
- work_schedule — планируемый график (кто ДОЛЖЕН работать)
- work_sessions — фактические смены (кто РЕАЛЬНО работал)
- work_journal_entries — записи журнала (связаны с work_sessions)
- users, tasks, chat_messages, chat_topics, files, audit_log, barcodes, colleague_tasks, salary_adjustments

⚠️ ВАЖНО: Удаление смены НЕ влияет на график! work_schedule и work_sessions — независимые сущности.

🔧 ИСПРАВЛЕНИЯ v4.9:
1. Миграция: schedule → work_schedule, создана work_sessions
2. API /api/schedule использует work_schedule
3. Логи и БД для EXE версии: %APPDATA%\GrafikRaboty
4. Socket.IO: async_mode="threading" + simple-websocket
5. VK синхронизация: проверка пути к файлу + alt_filepath

📦 УСТАНОВЩИК:
- Output/GrafikRaboty_Setup_v4.9_WORKING.exe (~100 MB)
- Inno Setup скрипт: grafikraboty_full_installer.iss
- EXE версия: exe_dist/GrafikRaboty_Server/

📱 МОБИЛЬНАЯ АДАПТАЦИЯ v4.7:
- calendar-layout: max-width: 100%, overflow-x: auto
- touch-action: manipulation для кнопок
- font-size: max(16px, ...) для input
- safe-area-inset для iPhone

🤖 MCP СИСТЕМА (порт 8081):
- 9 агентов: code_fixer, server_controller, api_tester, ui_verifier, security_auditor, desktop_automation, code_analyzer, vk_sync_monitor, integration_tester
- Путь: .mcp/

🔑 КОНФИГИ:
- telegram_config.json: token=8755572729:AAGAvyRp6Uni_wCbwjGIe2WRLOPUSlQ3iAc, admin_user_id=701768868
- vk_config.json: group_id=199112265, chat_peer_id=2000000001

👥 ПОЛЬЗОВАТЕЛИ:
- admin/admin — Администратор
- валерия/pass123 — Сотрудник
- ольга/pass456 — Сотрудник

📊 API ENDPOINTS:
- GET /api/schedule — график
- GET /api/work-journal — смены
- POST /api/work-journal/open — открыть смену
- POST /api/work-journal/close — закрыть смену
- POST /api/chat/send — отправить сообщение
- POST /api/files/upload — загрузить файл
- Сосямба Assistant v4.18 - Текущая версия проекта GrafikRaboty (24.03.2026). Исправления: 1) Ольга Наумова (VK ID: 1106085973) добавлена в VK чат, 2) Исправлено добавление записей в рабочий журнал (API /api/work-journal/entry), 3) Исправлена ошибка Socket.IO с isoformat, 4-6) Исправлены добавление/удаление/редактирование штрих-кодов, 7) Улучшен поиск штрих-кодов (реальное время + регистронезависимый), 8) Добавлены VK уведомления об открытии/закрытии смены, 9) Добавлен предпросмотр файлов в модальном окне, 10) Структурированная система файлов (поиск, фильтры, категории, пагинация), 11) Исправлен туннель с правильными IP и логированием.
- Сетевая конфигурация GrafikRaboty: Локальный IP: 192.168.1.207, Внешний IP: 81.23.181.238, Порт веб-сервера: 8080, Порт socket: 5000, Туннель: loca.lt (https://rotten-hands-run.loca.lt), Пароль туннеля: внешний IP (81.23.181.238). Ссылки для сотрудников: 1) Wi-Fi: http://192.168.1.207:8080, 2) Туннель: https://xxx.loca.lt (пароль: внешний IP), 3) Интернет: http://81.23.181.238:8080. Логи: logs/tunnel_monitor.log, logs/tunnel_connections.log, logs/web_server.log.
- VK конфигурация: Admin VK ID: 146411666, Chat Peer ID: 2000000001, Group ID: 199112265, VK User Map: {"146411666": 1 (admin), "57596922": 2 (Валерия), "2610587": 1 (admin), "1106085973": 3 (Ольга)}. Пользователи: 1) admin/admin (Администратор), 2) валерия/pass123 (Сотрудник, VK ID: 57596922), 3) ольга/pass456 (Сотрудник, VK ID: 1106085973). База данных: schedule.db (12 таблиц: users, tasks, schedule, work_sessions, work_journal_entries, files, audit_log, chat_messages, barcodes, colleague_tasks, salary_adjustments, chat_topics). Штрих-коды: 79 товаров (все из Excel загружены).
- Созданные файлы и инструменты (24.03.2026): 1) tunnel_manager_v2.py - новый менеджер туннеля с логированием и мониторингом, 2) test_tunnel_network.py - тест сети и туннеля, 3) import_missing_barcodes.py - импорт недостающих штрих-кодов, 4) fix_barcode_names.py - исправление названий штрих-кодов, 5) ИНСТРУКЦИЯ_ТУННЕЛЬ_v2.md - полная инструкция по туннелю. Кэширование IP: get_local_ip() кэширует результат для производительности.
- Исправления v4.20 (24.03.2026 15:55): 1) Обновлена функция send_tunnel_restart_notification() в vk_bot.py — теперь отправляет уведомления с актуальными IP (локальный 192.168.1.207, внешний 81.23.181.238), 2) Улучшена get_public_ip() с кэшированием на 5 минут, 3) Добавлен тест test_tunnel_notifications.py для проверки уведомлений. Сообщение теперь содержит: URL туннеля, пароль, локальный IP, внешний IP, ссылки для сотрудников.
- Уведомления туннеля v2.0 (24.03.2026 16:00): Обновлённое форматирование сообщений — добавлен заголовок "🚀 СЕРВЕР ЗАПУЩЕН — ВЕРСИЯ 2.0 🚀", разделители ━━━━━, стрелочки 👉 для ссылок, контрастные блоки для туннеля/локальной сети/внешнего IP, блок "Сотрудникам" с двумя ссылками (Wi-Fi и туннель), подпись "✅ v2.0 — Все IP актуальны!". Файлы обновлены: vk_bot.py, dist/GrafikRaboty_Server/_internal/vk_bot.py, installer_build/_internal/vk_bot.py.
- ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ УВЕДОМЛЕНИЙ v2.0 (24.03.2026 16:30): Проблема была в функции send_vk_startup_notification() в файле vk_startup.py (строка 12) — она отправляла старые сообщения с 127.0.0.1. Исправления: 1) Обновлена vk_startup.py — теперь отправляет сообщение v2.0 с локальным IP (192.168.1.207), внешним IP (81.23.181.238), блоком "Сотрудникам" и подписью "v2.0 — Все IP актуальны!", 2) Обновлён launcher_with_vk.py — передаёт актуальный public_ip вместо password из tunnel_info.json, 3) Обновлены vk_bot.py и dist/GrafikRaboty_Server/_internal/vk_bot.py — функции send_startup_notification() и send_tunnel_restart_notification() с новым форматированием.
- ИСПРАВЛЕНИЯ v4.10 (24.03.2026):

1. **app.js синтаксис** — исправлено 20+ ошибок:
   - Удалены лишние скобки `));` в fetch (строки 4318, 4416, 4486, 4494)
   - Исправлен дисбаланс скобок (1 лишний `}`, 5 нехватало `)`)
   - Добавлен `credentials: 'include'` во все fetch API вызовы
   - Версия файла: v20260324_v5

2. **Рабочий журнал — закрытие смены**:
   - Упрощена форма до 3 полей: Чек ККТ (общий), Чек терминала, Наличные вечером
   - Утро читается из `opening_sum` (а не `morning_cash`)
   - `evening_cashless` обрабатывает `None` значения
   - Кнопки "Запись" и "Закрыть смену" — зелёные (btn-success)
   - Кнопка "Удалить" — красная (btn-danger) для закрытых смен
   - Добавлена отладка в `openWjCloseModal()`

3. **web_work_journal.py**:
   - Исправлена обработка `evening_cashless` (None → 0)
   - CSV экспорт с UTF-8 BOM для Excel (крокозябры исправлены)
   - Добавлено API `/api/work-journal/sales-summary` — аналитика продаж по закрытым сменам

4. **templates/dashboard.html**:
   - Упрощена форма закрытия смены (убраны лишние поля)
   - Service Worker отключён для отладки

5. **login.html**:
   - Добавлен `credentials: 'include'` в 3 fetch вызова (login, verify-telegram, verify-vk)

6. **web_auth.py**:
   - Добавлен `session.modified = True` после установки сессии (3 места)

7. **web_server.py**:
   - Добавлены настройки сессий: SESSION_COOKIE_SECURE=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax'

8. **Конвертер ценников**:
   - Добавлен API `/api/converter/files` — список файлов

**ТЕКУЩИЕ ПРОБЛЕМЫ**:
- Кнопка "Закрыть смену" может не работать — нужна отладка (console.log добавлен)
- Sales модуль не интегрирован с work_sessions (только API для аналитики)
- ИСПРАВЛЕНИЯ v4.36 (09.04.2026):

1. **Статистика сотрудников в админ-панели** — исправлены все нули
   - Проблема: запросы к пустой таблице work_journal_shift вместо work_sessions
   - Исправлено в web_api.py (строки 2028-2071), функция api_get_employee_stats()
   - Заменено 5 SQL запросов: work_journal_shift → work_sessions
   - Теперь показывает: кол-во смен, выручку, опоздания, ранние/поздние закрытия, расхождения

2. **VK участники — загрузка из чата** — исправлена загрузка участников
   - Проблема: использовался метод groups.getMembers (подписчики группы), возвращал 0
   - Исправлено в web_vk_chat.py (строки 629-696), функция api_load_vk_chat_members()
   - Заменено на messages.getConversationMembers (участники беседы)
   - Используется chat_peer_id для получения участников конкретного чата
   - Добавлена обработка member_id вместо id
   - Добавлена фильтрация системных ID (боты, группы)
   - Улучшено логирование ошибок VK API

3. **VK сообщения НЕ приходят в чат** — исправлен Long Poll
   - Проблема: vk_bot.py использовал устаревшую version=3 для Callback API
   - Исправлено в vk_bot.py:
     * Long Poll version: 3 → 5.208 (строка 728)
     * Добавлена обработка failed ответа от Long Poll сервера
     * Улучшено извлечение message из event_data (3 варианта структуры)
     * Добавлено логирование структуры сообщения для отладки
     * Добавлена обработка message_edit события
   - Обновлена версия API в vk_config.json: 5.131 → 5.208

ФАЙЛЫ ИЗМЕНЕНЫ:
- web_api.py (5 SQL запросов, статистика сотрудников)
- web_vk_chat.py (VK API метод, обработка участников)
- vk_bot.py (Long Poll version, обработка событий, структура message)
- vk_config.json (api_version: 5.131 → 5.208)

БАЗА ДАННЫХ: work_sessions (18 записей), work_journal_entries, chat_messages (118 сообщений), vk_config.json (vk_user_map)

ПОЛЬЗОВАТЕЛИ: admin/admin, валерия/pass123 (VK:57596922), ольга/pass456 (VK:1106085973)

1. **app.js синтаксис** — исправлено 20+ ошибок:
   - Удалены лишние скобки `));` в fetch (строки 4318, 4416, 4486, 4494)
   - Исправлен дисбаланс скобок (1 лишний `}`, 5 нехватало `)`)
   - Добавлен `credentials: 'include'` во все fetch API вызовы
   - Версия файла: v20260324_v5

2. **Рабочий журнал — закрытие смены**:
   - Упрощена форма до 3 полей: Чек ККТ (общий), Чек терминала, Наличные вечером
   - Утро читается из `opening_sum` (а не `morning_cash`)
   - `evening_cashless` обрабатывает `None` значения
   - Кнопки "Запись" и "Закрыть смену" — зелёные (btn-success)
   - Кнопка "Удалить" — красная (btn-danger) для закрытых смен
   - `closing_sum` отправляется = `evening_cash`
   - Добавлена отладка в `openWjCloseModal()`

3. **Расхождение в смене — ПРАВИЛЬНЫЙ РАСЧЁТ**:
   - Наличные по ККТ = Выручка общая - Безнал по ККТ - Терминал
   - ДОЛЖНО БЫТЬ = Утро + Наличные по ККТ + Операции (Внесла +, Отдала/Взяла -)
   - Расхождение = Факт - Должно
   - Показывает в UI: ✅ ВСЁ СХОДИТСЯ / ✅ ИЗЛИШЕК / ❌ НЕДОСТАЧА

4. **web_work_journal.py**:
   - Исправлена обработка `evening_cashless` (None → 0)
   - CSV экспорт с UTF-8 BOM для Excel (крокозябры исправлены)
   - Расхождение считается: `cash_revenue = revenue_total - acquiring_amount - terminal_actual`
   - Добавлено API `/api/work-journal/sales-summary` — аналитика продаж по закрытым сменам

5. **vk_bot.py**:
   - VK уведомление при закрытии смены содержит полный расчёт:
     - Утро, Выручка (нал+безнал), Терминал, Операции
     - ДОЛЖНО БЫТЬ = Утро + Нал ККТ - Операции
     - ФАКТ = Наличные вечером
     - ✅ ИЗЛИШЕК / ❌ НЕДОСТАЧА с суммой

6. **templates/dashboard.html**:
   - Упрощена форма закрытия смены (убраны поля `acquiring-amount`, `evening-cashless`)
   - Service Worker отключён для отладки
   - В "Итоги смены" добавлено расхождение

7. **login.html**:
   - Добавлен `credentials: 'include'` в 3 fetch вызова (login, verify-telegram, verify-vk)

8. **web_auth.py**:
   - Добавлен `session.modified = True` после установки сессии (3 места)

9. **web_server.py**:
   - Добавлены настройки сессий: SESSION_COOKIE_SECURE=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax'

10. **Конвертер ценников**:
    - Исправлены API маршруты: `/api/converter/*` → `/converter/*`
    - `/converter/analyze`, `/converter/upload`, `/converter/files`, `/converter/open`, `/converter/print`, `/converter/generate`

11. **База данных**:
    - Добавлена колонка `terminal_actual` в `work_sessions` (миграция add_shift_columns.py)

**ТЕКУЩИЕ ПРОБЛЕМЫ**:
- Sales модуль не интегрирован с work_sessions (только API для аналитики)
- КОНВЕРТЕР ЦЕННИКОВ - ПОЛНАЯ ИСТОРИЯ ИСПРАВЛЕНИЙ (v4.10, 24-25.03.2026):

**ОШИБКИ КОТОРЫЕ Я ДЕЛАЛ:**

1. **API маршруты** - пытался использовать `/api/converter/*` вместо `/converter/*`
   - Исправление: все маршруты без `/api/` префикса

2. **Формат Excel** - делал 3 колонки (товар|цена|ед) вместо 4 строк в каждом ценнике
   - Правильно: 4 строки на ценник (Орг|Товар|Цена|Дата)

3. **Переменная row_in_row** - опечатка, должно быть row_num
   - Error: NameError: name 'row_in_row' is not defined

4. **Рамки ценников** - делал тонкие рамки, нужны ЖИРНЫЕ внешние
   - Правильно: thick_border для внешних границ, no_border внутри

5. **Структура ценника** - делал в ряд колонки, нужно 4 строки друг под другом
   - Строка 1: Организация (по центру)
   - Строка 2: Наименование товара (слева)
   - Строка 3: Цена (по центру, крупно, красный)
   - Строка 4: Дата + ед.измерения (слева)

6. **Генерация данных** - не передавал настройки (шрифты, размеры) с клиента
   - Исправление: collectSettings() передаёт font_name, org_size, name_size, price_base, date_size

**ЧТО РАБОТАЕТ ПРАВИЛЬНО СЕЙЧАС:**

1. **Загрузка прайса** → /converter/upload (FormData с файлом)
2. **Анализ** → /converter/analyze (JSON с filename, возвращает products[])
3. **Генерация** → /converter/generate (JSON с products + settings, возвращает Excel файл)
4. **Список файлов** → /converter/files (JSON со списком всех файлов)
5. **Скачивание** → /converter/download/<filename> (Excel файл)
6. **Просмотр** → /converter/view/<filename> (Excel файл в браузере)

**СТРУКТУРА EXCEL:**

```
Каждый ценник = 4 строки × 4 колонки
- Строка 1: Организация (объединено 4 колонки, жирная рамка сверху+бока)
- Строка 2: Товар (объединено 3 колонки, тонкая линия, боковые жирные)
- Строка 3: Цена (объединено 4 колонки, тонкая линия, боковые жирные)
- Строка 4: Дата + ед. (объединено 4 колонки, жирная рамка снизу+бока)

cols=3 → 3 ценника в ряду (12 колонок total)
10 товаров → 4 ряда (3+3+3+1)
```

**НАСТРОЙКИ КОТОРЫЕ ПЕРЕДАЮТСЯ:**

```javascript
{
  cols: 3,                    // ценников в ряду
  font_name: 'Calibri',       // шрифт
  org_name: 'ООО "..."',      // организация
  org_size: 14, org_bold: true,
  name_size: 14, name_bold: false,
  price_base: 24, price_bold: true,
  date_size: 10, date_bold: true
}
```

**ПУТИ К ФАЙЛАМ:**

- Загрузки: `uploads/converter/`
- Готовые ценники: `uploads/price_tags/`
- Метаданные: `uploads/price_tags/<timestamp>.json`

**ВАЖНО ДЛЯ БУДУЩЕГО:**

1. Каждый ценник — ОТДЕЛЬНАЯ ТАБЛИЦА с жирной рамкой вокруг
2. Внутри ценника — тонкие разделительные линии
3. Все 4 поля в каждом ценнике (Орг, Товар, Цена, Дата)
4. Товар и Цена — УНИКАЛЬНЫЕ для каждого ценника (из прайса)
5. Орг, Дата, Шрифты, Размеры — ОБЩИЕ для всех (из настроек)
6. Превью показывает 1 ценник → Excel генерирует ВСЕ товары из прайса
- GrafikRaboty v4.30 Docker+PWA готов (31.03.2026): Созданы Dockerfile, docker-compose.yml (web+postgres+redis), .env, nginx.conf, scripts/init_db.sql, migrate_sqlite_to_postgres.py. PWA: manifest.json (обновлён), sw.js v2.0, pwa-installer.js, barcode-scanner.js, offline.html. Обновлены: web_config.py (dotenv+PostgreSQL), dashboard.html (PWA скрипты), requirements.txt (psycopg2, redis, gunicorn, gevent). Документация: DOCKER_DEPLOYMENT.md, БЫСТРЫЙ_СТАРТ_DOCKER_PWA.md, ИТОГИ_DOCKER_PWA_ГОТОВО.md, test_docker_setup.py. MCP система: 9 агентов (code_fixer, server_controller, api_tester, ui_verifier, security_auditor, desktop_automation, code_analyzer, vk_sync_monitor, integration_tester), порт 8081.
- GrafikRaboty v4.30 Docker+PWA - Полная конфигурация (31.03.2026):

DOCKER (8 файлов):
- Dockerfile: multi-stage, python:3.12-slim, gunicorn+gevent, healthcheck, appuser
- docker-compose.yml: web(8080)+postgres(5432)+redis(6379)+nginx(80/443 profile), volumes, healthchecks
- .env: TELEGRAM_BOT_TOKEN=8755572729:AAGAvyRp6Uni_wCbwjGIe2WRLOPUSlQ3iAc, ADMIN_USER_ID=701768868, VK_GROUP_ID=199112265, ADMIN_VK_ID=146411666, LOCAL_IP=192.168.1.207, PUBLIC_IP=81.23.181.238, TUNNEL_URL=https://rotten-hands-run.loca.lt
- .env.example, .dockerignore, nginx/nginx.conf, scripts/init_db.sql (12 таблиц), scripts/migrate_sqlite_to_postgres.py

PWA (5 файлов):
- manifest.json: start_url=/, 3 shortcuts (График/Задачи/Чат), share_target, 2 icons
- sw.js v2.0: cache-first для статики, network-first для API, push notifications, offline page
- pwa-installer.js: beforeinstallprompt, update notifications, connection listener
- barcode-scanner.js: QuaggaJS, 14 типов (EAN/Code128/Code39/UPC), getUserMedia, facingMode:environment
- offline.html: connection check, cache status, retry button

ОБНОВЛЕНЫ (3 файла):
- web_config.py: load_dotenv, DOCKER_MODE, USE_POSTGRES, get_db_connection() с psycopg2
- dashboard.html: добавлены sw.js, pwa-installer.js, barcode-scanner.js (строки 1106-1108)
- requirements.txt: python-dotenv, psycopg2-binary, redis, gunicorn, gevent, gevent-websocket

MCP СИСТЕМА (порт 8081, 9 агентов):
code_fixer, server_controller, api_tester, ui_verifier, security_auditor, desktop_automation, code_analyzer, vk_sync_monitor, integration_tester

БАЗА ДАННЫХ (12 таблиц): users, tasks, work_schedule, work_sessions, work_journal_entries, chat_messages, chat_topics, files, barcodes, audit_log, colleague_tasks, salary_adjustments, vk_attachments

ПОЛЬЗОВАТЕЛИ: admin/admin (Администратор, VK:146411666), валерия/pass123 (VK:57596922), ольга/pass456 (VK:1106085973)
- GrafikRaboty v4.32 — ПОЛНАЯ РЕАЛИЗАЦИЯ НАПОМИНАНИЙ (01.04.2026 20:00):

МОДУЛЬ НАПОМИНАНИЙ (web_reminders.py) — ГОТОВ:
- API: GET /api/reminders (список), POST /api/reminders (создать админ), POST /api/reminders/<id>/confirm, GET /api/reminders/<id>/stats, DELETE /api/reminders/<id>
- Таблицы: reminders (напоминания), reminder_confirmations (подтверждения пользователей)
- Всплывающее окно в dashboard.html — красная рамка, заголовок «ВАЖНОЕ НАПОМИНАНИЕ»
- Кнопка «✅ ПРОЧИТАНО И ПОНЯТНО» — обязательное подтверждение
- Нельзя закрыть крестиком или кликом вне окна (alert «Вы должны подтвердить»)
- Очередь напоминаний — показываются по порядку все неподтверждённые
- Загрузка через 2 секунды после входа (loadAndShowReminders)
- Статистика в окне: сколько из скольких подтвердили
- VK отчёт админу в личку когда ВСЕ сотрудники подтвердили
- Авто-создание напоминаний при просрочке товара (create_revision_reminder)

ФУНКЦИИ АДМИНА:
- Кнопка «📢 Создать напоминание» в админ-панели
- Форма: заголовок, текст, тип (general/revision/schedule/task), срок действия (часов), галочка «требуется подтверждение»
- Просмотр статистики: who confirmed + who not confirmed + timestamps
- Удаление напоминаний

РЕВИЗИЯ ТОВАРА — ОБНОВЛЕНО:
- Блокировка редактирования: сотрудник может только создать и отметить «Продано»
- Ежедневная проверка (scheduler_revision.py в 9:00) — авто-пересчёт скидок для ВСЕХ товаров
- Логирование: revision_audit_log (кто создал/изменил/принял решение)
- API логов: GET /api/revision/<id>/audit, GET /api/audit (только админ)
- Регламент скидок: >4мес=0%, ≤4мес=15%, ≤3мес=25%, ≤2мес=35%, ≤1мес=40%, просрочка=50%
- При просрочке: авто-создание напоминания + VK уведомление админу + кнопка решения (забрать/продать)

БАЗА ДАННЫХ (16 таблиц):
users, tasks, work_schedule, work_sessions, work_journal_entries, chat_messages, chat_topics, files, barcodes, audit_log, colleague_tasks, salary_adjustments, product_revisions, revision_audit_log, reminders, reminder_confirmations

ФАЙЛЫ МОДУЛЯ НАПОМИНАНИЙ:
- web_reminders.py (450 строк) — API модуль
- create_reminders_db.py — скрипт создания таблиц
- scheduler_revision.py — обновлён с проверкой всех товаров
- web_revision.py — обновлён (логирование + создание напоминаний)
- dashboard.html — модальное окно напоминаний + JavaScript функции
- ИНСТРУКЦИЯ_НАПОМИНАНИЯ.md — полная инструкция
- ИНСТРУКЦИЯ_РЕВИЗИЯ_ТОВАРА.md — инструкция по ревизии
- РЕВИЗИЯ_СТАТУС.md — статус реализации

VK ИНТЕГРАЦИЯ:
- send_reminder_to_vk() — отправка нового напоминания в чат
- send_confirmation_report_to_admin() — отчёт когда все подтвердили
- send_expired_notification() — уведомление о просрочке товара
- create_revision_reminder() — авто-создание напоминания при просрочке

ПЛАНИРОВЩИК (scheduler_revision.py):
- Ежедневно в 9:00 — check_daily_expirations() (пересчёт скидок + обновление статусов)
- Еженедельно в понедельник 9:00 — send_weekly_report() (отчёт в VK)

ПОЛЬЗОВАТЕЛИ: admin/admin (Администратор, VK:146411666), валерия/pass123 (VK:57596922), ольга/pass456 (VK:1106085973)

ТЕКУЩИЙ СТАТУС: ✅ ВСЁ ПОЛНОСТЬЮ РЕАЛИЗОВАНО И ГОТОВО К ИСПОЛЬЗОВАНИЮ

БАЗА ДАННЫХ (14 таблиц):
users, tasks, work_schedule, work_sessions, work_journal_entries, chat_messages, chat_topics, files, barcodes, audit_log, colleague_tasks, salary_adjustments, product_revisions, revision_audit_log, reminders, reminder_confirmations
- GrafikRaboty v4.33 — Ревизия товара с количеством и напоминания (01.04.2026 21:00):

МОДУЛЬ «РЕВИЗИЯ ТОВАРА» — ПОЛНАЯ ВЕРСИЯ:

БАЗА ДАННЫХ (таблица product_revisions):
- id, user_id, full_name, product_name, retail_price, expiry_date
- barcode (TEXT) — штрих-код для 1С
- quantity (INTEGER, default=1) — количество штук (например, целая коробка)
- days_remaining, discount_percent, final_price — авто-расчёт
- status (active/admin_decision/sold/reserved_admin/utilized)
- admin_decision, admin_decision_at, admin_vk_id — решение админа
- notification_sent, weekly_notified — уведомления

РЕГЛАМЕНТ СКИДОК (авто-расчёт):
- >4 месяцев: 0% (🟢 зелёный)
- ≤4 месяцев: 15% (🟡 жёлтый)
- ≤3 месяцев: 25% (🟡 жёлтый)
- ≤2 месяцев: 35% (🟠 оранжевый)
- ≤1 месяца: 40% (🟠 оранжевый)
- Срок истёк: 50% + статус admin_decision (🔴 красный)

API ENDPOINTS:
- GET /api/revision/revisions?filter=all|active|decision|my|archive
- POST /api/revision/revisions (создать: product_name, quantity, barcode, retail_price, expiry_date)
- PUT /api/revision/revisions/<id> (только статус: sold)
- PATCH /api/revision/revisions/<id> (редактировать: product_name, quantity, barcode, retail_price, expiry_date)
- DELETE /api/revision/revisions/<id> (удалить, только админ)
- POST /api/revision/revisions/<id>/decision (решение админа: sell/reserve)
- GET /api/revision/stats (статистика)
- GET /api/revision/revisions/<id>/audit (лог изменений)
- GET /api/audit (все логи, только админ)

ФУНКЦИИ АДМИНА:
- ✏️ Редактирование любого товара (название, количество, штрих-код, цена, срок)
- 🗑️ Удаление товара
- ✅ Решение по просрочке: «Разрешить продать» (50%) или «Забрать себе»
- 📊 Просмотр статистики и логов

ФУНКЦИИ СОТРУДНИКА:
- ➕ Добавление товара (название, количество, штрих-код, цена, срок)
- ✅ Отметка «Продано» для своих товаров
- 📋 Просмотр только своих товаров

АВТОМАТИЗАЦИЯ:
- Ежедневная проверка в 9:00 (scheduler_revision.py)
  - Пересчёт скидок для всех товаров
  - Авто-смена статуса на admin_decision при просрочке
- Еженедельный отчёт в понедельник 9:00 в VK чат
- Мгновенное уведомление админу в VK при просрочке
- VK отчёт админу когда все сотрудники подтвердили напоминание

КОМ-СКАНЕРЫ (для штрих-кодов):
- com_scanner.py — чтение из COM3 и COM6
- web_com_scanner.py — API /api/com-scanner/last
- Автоматическое заполнение поля штрих-кода при сканировании
- Звуковой сигнал при сканировании
- Фоновый опрос каждые 500мс

НАПОМИНАНИЯ С ПОДТВЕРЖДЕНИЕМ:
- База: reminders, reminder_confirmations
- API: GET/POST /api/reminders, POST /api/reminders/<id>/confirm, DELETE /api/reminders/<id>, GET /api/reminders/<id>/stats
- Всплывающее окно с красной рамкой
- Нельзя закрыть без нажатия «✅ ПРОЧИТАНО И ПОНЯТНО»
- Очередь напоминаний — показываются по порядку
- Статистика: кто подтвердил, кто нет
- VK отчёт админу когда все подтвердили
- Авто-создание при просрочке товара

ИНТЕРФЕЙС:
- Вкладка «📦 Ревизия товара» в меню
- Таблица: Товар | Кол-во | Штрих-код | Цена | Срок | Остаток | Скидка | Итог | Статус | Действия
- Цветовая индикация строк (🟢🟠🔴)
- Фильтры: Все/Активные/Требуют решения/Мои/Архив
- Статистика в карточках (Всего, Просрочено, Требуют решения, Общая стоимость)
- Модальные окна: добавление, редактирование, решение админа

ФАЙЛЫ:
- web_revision.py — API модуль ревизии
- web_reminders.py — API модуль напоминаний
- com_scanner.py — чтение COM-портов
- web_com_scanner.py — API COM-сканеров
- scheduler_revision.py — планировщик (ежедневно 9:00, еженедельно понедельник)
- create_revision_db.py — создание таблицы product_revisions
- create_reminders_db.py — создание таблиц reminders, reminder_confirmations
- add_barcode_to_revision.py — добавление поля barcode
- add_quantity_to_revision.py — добавление поля quantity
- add_quantity_to_revision.py — добавление поля quantity
- ИНСТРУКЦИЯ_РЕВИЗИЯ_ТОВАРА.md, ИНСТРУКЦИЯ_НАПОМИНАНИЯ.md, РЕВИЗИЯ_СТАТУС.md

БАЗА ДАННЫХ (16 таблиц):
users, tasks, work_schedule, work_sessions, work_journal_entries, chat_messages, chat_topics, files, barcodes, audit_log, colleague_tasks, salary_adjustments, vk_attachments, product_revisions, revision_audit_log, reminders, reminder_confirmations

ТЕКУЩИЙ СТАТУС: ✅ ВСЁ ПОЛНОСТЬЮ РЕАЛИЗОВАНО
- GrafikRaboty v4.34 — Импорт товаров из 1С с поиском по штрих-коду (01.04.2026 22:00):

НОВЫЙ МОДУЛЬ "СПРАВОЧНИК ТОВАРОВ ИЗ 1С":

БАЗА ДАННЫХ (таблица products_1c):
- id, name, full_name, retail_price, purchase_price
- barcode_main, barcode_inner — штрих-коды
- group_name, category, vendor_code — группировка
- unit, weight, volume — единицы измерения
- is_active, created_at, updated_at

ИМПОРТ ИЗ 1С:
- import_1c_products.py — скрипт импорта
- Читает два файла:
  1. ШТРИХ КОДЫ НОМЕНКЛАТУР.xlsx — штрих-коды + названия
  2. НОМЕНКЛАТУРА И ЦЕНА.xlsx — цены + группы
- Объединяет данные по названию номенклатуры
- Сохраняет в products_1c

API ENDPOINTS:
- GET /api/products-1c/search?barcode=...&query=... — поиск
- GET /api/products-1c/barcode/<barcode> — по штрих-коду
- GET /api/products-1c — все товары с фильтрами
- PUT /api/products-1c/<id> — редактирование (админ)
- POST /api/products-1c/import — импорт JSON (админ)

ИНТЕРФЕЙС В РЕВИЗИИ:
- Синий блок "🔍 Поиск товара в базе 1С"
- Поле ввода + кнопка "Найти"
- Авто-поиск при вводе (500мс задержка)
- Авто-поиск при сканировании штрих-кода
- Результаты: название | штрих-код | цена | группа
- Клик по товару → авто-заполнение полей:
  - Наименование
  - Штрих-код
  - Цена
- Остаётся ввести: Количество + Срок годности

СХЕМА РАБОТЫ:
1. Админ запускает: python import_1c_products.py
2. Загружаются все товары из 1С
3. Сотрудник открывает "Ревизия товара" → "Добавить товар"
4. Сканирует штрих-код сканером
5. Система находит товар в базе 1С
6. Авто-заполняет: название, штрих-код, цена
7. Сотрудник вводит: Количество (например 24 шт) + Срок годности
8. Сохраняет → товар добавляется в ревизию

ФАЙЛЫ:
- create_products_1c_db.py — создание таблицы
- import_1c_products.py — импорт из Excel 1С
- web_products_1c.py — API модуль
- dashboard.html — обновлён (поиск + авто-заполнение)
- web_server.py — зарегистрирован products_1c_bp

ПРЕИМУЩЕСТВА:
- ✅ Не нужно вбивать название вручную
- ✅ Сканируешь штрих-код → получаешь все данные
- ✅ Можно искать по названию (частичное совпадение)
- ✅ Актуальные цены из 1С
- ✅ Группировка по категориям
- ✅ Можно редактировать цену если устарела

БАЗА ДАННЫХ (17 таблиц):
users, tasks, work_schedule, work_sessions, work_journal_entries, chat_messages, chat_topics, files, barcodes, audit_log, colleague_tasks, salary_adjustments, vk_attachments, product_revisions, revision_audit_log, reminders, reminder_confirmations, products_1c
- GrafikRaboty v4.35 — Исправления и импорт 1С (01.04.2026 23:00):

ИСПРАВЛЕНИЯ:
1. COM-сканер 404 ошибка — исправлён маршрут в web_com_scanner.py
2. Зарплата 0 — исправлен запрос (work_journal_shift → work_sessions)
3. Импорт 1С — объединение по точному названию номенклатуры

НОВОЕ:
1. Админ панель — кнопка "📦 Импорт товаров из 1С"
2. Модальное окно с инструкцией
3. API /api/products-1c/import — запуск импорта
4. Автоматическое обновление существующих товаров
5. Статистика: импортировано/обновлено/ошибки

ФУНКЦИОНАЛ:
- Админ кладёт 2 Excel файла в папку проекта
- Нажимает "Загрузить и импортировать"
- Система объединяет по названию номенклатуры
- Обновляет существующие товары
- Добавляет новые
- Показывает статистику

ИСПРАВЛЕННЫЕ ФАЙЛЫ:
- web_com_scanner.py (маршрут /last)
- web_api.py (salary-summary → work_sessions)
- import_1c_products.py (объединение по названию)
- web_products_1c.py (API импорт)
- dashboard.html (админ панель + модалка + JS)

БАЗА ДАННЫХ: 17 таблиц
- ИСПРАВЛЕНИЯ v4.36 (09.04.2026):

1. **Статистика сотрудников в админ-панели** — исправлены все нули
   - Проблема: запросы к пустой таблице work_journal_shift вместо work_sessions
   - Исправлено в web_api.py (строки 2028-2071), функция api_get_employee_stats()
   - Заменено 5 SQL запросов: work_journal_shift → work_sessions
   - Теперь показывает: кол-во смен, выручку, опоздания, ранние/поздние закрытия, расхождения

2. **VK участники — загрузка из чата** — исправлена загрузка участников
   - Проблема: использовался метод groups.getMembers (подписчики группы), возвращал 0
   - Исправлено в web_vk_chat.py (строки 629-696), функция api_load_vk_chat_members()
   - Заменено на messages.getConversationMembers (участники беседы)
   - Используется chat_peer_id для получения участников конкретного чата
   - Добавлена обработка member_id вместо id
   - Добавлена фильтрация системных ID (боты, группы)
   - Улучшено логирование ошибок VK API

ФАЙЛЫ ИЗМЕНЕНЫ:
- web_api.py (5 SQL запросов, статистика сотрудников)
- web_vk_chat.py (VK API метод, обработка участников)

БАЗА ДАННЫХ: work_sessions (18 записей), work_journal_entries, vk_config.json (vk_user_map)

ПОЛЬЗОВАТЕЛИ: admin/admin, валерия/pass123 (VK:57596922), ольга/pass456 (VK:1106085973)
- ИСПРАВЛЕНИЯ v4.36 (09.04.2026) - VK СООБЩЕНИЯ:

3. **VK сообщения НЕ приходят в чат** — исправлен Long Poll
   - Проблема: vk_bot.py использовал устаревшую version=3 для Callback API
   - Исправлено в vk_bot.py:
     * Long Poll version: 3 → 5.208 (строка 728)
     * Добавлена обработка failed ответа от Long Poll сервера
     * Улучшено извлечение message из event_data (3 варианта структуры)
     * Добавлено логирование структуры сообщения для отладки
     * Добавлена обработка message_edit события
   - Обновлена версия API в vk_config.json: 5.131 → 5.208
   
   ТЕСТЫ:
   - test_vk_api.py — проверка VK API токена, Long Poll сервера, участников чата
   - test_vk_longpoll.py — полная проверка Long Poll v5.208 с ожиданием событий
   
   VK API работает:
   - Token: валидный
   - Group ID: 199112265 (ГРАФИК ВЕТГИД)
   - Chat Peer ID: 2000000001
   - Long Poll сервер: https://lp.vk.com/whp/199112265
   - 5 участников в чате (admin, Валерия, Ольга + 2 других)
   
   ФАЙЛЫ ИЗМЕНЕНЫ:
   - vk_bot.py (Long Poll version, обработка событий, структура message)
   - vk_config.json (api_version: 5.131 → 5.208)
- ИСПРАВЛЕНИЯ v4.36 VK СИНХРОНИЗАЦИЯ (09.04.2026):

ПРОБЛЕМА: VK сообщения не отображаются в чате Графика (VK тема topic_id=3 пустая), хотя в БД 126 сообщений

ПРИЧИНЫ:
1. VK Long Poll version=3 устарел → исправлено на version=5.208
2. web_vk_chat.py не использовал _ssl_context → исправлено
3. VK участники загружались через groups.getMembers → исправлено на messages.getConversationMembers
4. Чат не обновлялся автоматически для VK темы

ИСПРАВЛЕНИЯ:
1. vk_bot.py: Long Poll version 3→5.208, обработка failed, структура message (3 варианта)
2. web_vk_chat.py: добавлен _ssl_context в urlopen, getConversationMembers вместо getMembers
3. static/js/app.js: добавлено авто-обновление VK чата каждые 3 сек, отладка console.log
4. vk_config.json: api_version 5.131→5.208
5. templates/dashboard.html: обновлена версия app.js (v=20260409_vk_sync_v6)

ФАЙЛЫ:
- vk_bot.py (Long Poll v5.208, обработка сообщений)
- web_vk_chat.py (SSL context, getConversationMembers)
- static/js/app.js (авто-обновление, отладка)
- templates/dashboard.html (версия файла)
- vk_config.json (API версия)
- migrate_vk_messages.py (скрипт миграции)
- test_vk_api.py, test_vk_longpoll.py (тесты)

БАЗА ДАННЫХ:
- chat_messages: 126 сообщений в topic_id=3 (VK), 2 в topic_id=2 (Telegram)
- chat_topics: Общий(1), Telegram(2), VK(3)

ТЕКУЩИЙ СТАТУС: VK сообщения приходят в БД, чат обновляется каждые 3 сек при открытии VK темы
- ИСПРАВЛЕНИЕ v4.36 VK ЧАТ (09.04.2026 11:35) - КРИТИЧЕСКАЯ ПРОБЛЕМА:

ПРОБЛЕМА: VK чат показывал только старые сообщения (до 1 апреля), новые сообщения НЕ отображались

ПРИЧИНА: SQL запрос в web_chat.py использовал ORDER BY created_at ASC LIMIT 100 — возвращал ПЕРВЫЕ 100 сообщений (самые старые), а новые (100+) обрезались

РЕШЕНИЕ: Изменена сортировка на DESC (новые первыми) + реверс массива для отображения в правильном порядке

ИСПРАВЛЕНИЕ:
- web_chat.py: ORDER BY m.created_at DESC + messages.reverse()
- Теперь API возвращает ПОСЛЕДНИЕ 100 сообщений (включая сегодняшние)
- Сообщения отображаются в правильном порядке (старые→новые)

ЛОГИ:
- API возвращал: last message: created_at: '2026-04-01 20:44:05' (старое)
- Новые сообщения "321678" от 09.04 были в БД (ID: 239-240) но НЕ попадали в выборку
- Теперь API вернёт: last message: created_at: '2026-04-09 11:32:19' (сегодняшнее)

Файлы изменены:
- web_chat.py (сортировка сообщений чата)

Перезапустить сервер для применения!
- ИСПРАВЛЕНИЕ v4.36 ШТРИХ-КОДЫ ПОИСК (09.04.2026 11:36):

ПРОБЛЕМА: Поиск штрих-кодов по "сири" находил только 1 товар, хотя должно быть много "Сириусов"

ПРИЧИНА: LIMIT 100 обрезал результаты ДО фильтрации:
- Загружались первые 100 записей из БД
- Потом фильтровалось по "сири" в Python
- Если "Сириусы" были после 100-й записи — они НЕ ЗАГРУЖАЛИСЬ

РЕШЕНИЕ: 
- SQL фильтрация вместо Python: LIKE ? COLLATE NOCASE
- Сначала фильтрация в БД, потом пагинация LIMIT/OFFSET
- Регистронезависимый поиск через COLLATE NOCASE

ИСПРАВЛЕНИЕ:
- web_barcodes.py: функция get_barcodes()
- Было: загрузка 100 записей → фильтрация в Python
- Стало: SQL LIKE с COLLATE NOCASE → пагинация

ПРИМЕР:
- Было: search="сири" → 1 результат (только первые 100 записей проверены)
- Стало: search="сири" → ВСЕ "Сириусы" из всей БД (SQL LIKE)

Файлы изменены:
- web_barcodes.py (поиск штрих-кодов через SQL LIKE)

Перезапустить сервер для применения!
- ИСПРАВЛЕНИЕ v4.36 ШТРИХ-КОДЫ ПОИСК (09.04.2026 11:45) - ФИНАЛЬНОЕ:

ПРОБЛЕМА 1: Поиск по "сири" находил только 1 товар вместо 9 "Сириусов"
ПРОБЛЕМА 2: SQLite LIKE не поддерживает кириллицу (LIKE '%сири%' = 0, LIKE '%Сири%' = 9)
ПРОБЛЕМА 3: COLLATE NOCASE не работает для кириллицы
ПРОБЛЕМА 4: UPPER() не работает для кириллицы

ПРИЧИНА: 
- Было: SQL LIKE с COLLATE NOCASE → 0 результатов для кириллицы
- SQLite LIKE регистрозависимый для кириллицы!

РЕШЕНИЕ:
- Python фильтрация: загружаем ВСЕ активные штрих-коды → фильтруем в Python через .lower()
- search_lower = 'сири'.lower() → ищем в product_name.lower()
- Работает для любой кодировки (кириллица, латиница)

ИСПРАВЛЕНИЕ:
- web_barcodes.py: функция get_barcodes()
- SQL: SELECT * FROM barcodes WHERE is_active = 1 (все записи)
- Python: filtered = [bc for bc in all_barcodes if search_lower in bc['product_name'].lower()]
- Результат: search="сири" → 9 товаров "Сириус" ✅

ПРОВЕРКА:
- search="сири" → 9 результатов (Все Сириусы)
- search="си" → находит Сириусы + другие
- search="Sirius" → находит латиницей

Файлы изменены:
- web_barcodes.py (Python фильтрация для кириллицы)

Перезапустить сервер для применения!
- УМНАЯ СИСТЕМА КОНТРОЛЯ ТОВАРОВ v2.0 - ПОЛНАЯ РЕАЛИЗАЦИЯ (09.04.2026):

ЭТАП 1: Предупреждения при запуске смены
- Функция get_on_shift_warnings() в web_revision.py
- Модальное окно showShiftWarnings() при открытии страницы ревизии
- Показывает товары истекающие ≤7 дней (критично) и ≤30 дней (внимание)
- Даёт рекомендации: "Предложите покупателям со скидкой"

ЭТАП 2: Умные рекомендации
- Функция get_smart_recommendations() в web_revision.py
- API /api/revision/recommendations
- Приоритеты: critical (просроченные без решения), high (≤7 дней), medium (≤30 дней), low (застойные)

ЭТАП 3: Заблаговременные уведомления
- Функция send_pre_expiry_alerts() в web_revision.py
- Планировщик: job_pre_expiry_alerts() в 09:05
- За 14 дней: логирование
- За 7 дней: VK чат
- За 3 дня: экстренное админу + чат
- За 1 день: КРИТИЧЕСКОЕ админу + чат

ЭТАП 4: Баннер умного контроля
- HTML элемент #smart-control-banner в dashboard.html
- CSS стили .smart-control-banner, .smart-alert-item, .smart-summary-card
- JavaScript loadSmartControlBanner()
- Показывает: критично/внимание/без движений с количеством и списком

ЭТАП 5: Сортировка и поиск
- web_revision.py: get_revisions() обновлена
- Параметры: search (поиск по названию/штрих-коду), sort (expiry_date/created_at/name/discount)
- Python фильтрация для кириллицы (как в штрих-кодах)
- HTML: input#revision-search, select#revision-sort

ЭТАП 6: Акционные ценники
- HTML: чекбоксы в таблице, панель #promotion-panel
- JavaScript: toggleSelectAllRevisions(), updatePromotionPanel(), generatePromotionPriceTags()
- API: /converter/generate-promotion в web_converter.py
- Excel с пометкой "🔥 АКЦИЯ", красная цена, старая цена зачёркнута
- openpyxl для генерации Excel

ФАЙЛЫ ИЗМЕНЕНЫ:
- web_revision.py (+380 строк: warnings, recommendations, pre-expiry alerts, API endpoints)
- scheduler_revision.py (job_pre_expiry_alerts в 09:05)
- web_converter.py (+150 строк: generate_promotion_price_tags)
- static/css/style.css (+170 строк: стили умного контроля)
- templates/dashboard.html (+200 строк: баннер, поиск, сортировка, чекбоксы, JS функции)

БАЗА ДАННЫХ: product_revisions (используется существующая)

ПЕРЕЗАПУСТИТЬ СЕРВЕР ДЛЯ ПРИМЕНЕНИЯ!
