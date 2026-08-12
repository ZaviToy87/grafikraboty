# 🐳 DOCKER DEPLOYMENT GUIDE
## GrafikRaboty v4.30 - Docker + PostgreSQL + PWA

---

## 📋 ОГЛАВЛЕНИЕ

1. [Что такое Docker и зачем он нужен](#что-такое-docker)
2. [Быстрый старт](#быстрый-старт)
3. [Архитектура приложения](#архитектура)
4. [Настройка окружения](#настройка-окружения)
5. [Запуск в Docker](#запуск-в-docker)
6. [Миграция данных из SQLite](#миграция-данных)
7. [PWA - Установка на телефон](#pwa-установка)
8. [Production развертывание](#production-развертывание)
9. [Команды Docker](#команды-docker)
10. [Решение проблем](#решение-проблем)

---

## 🎯 ЧТО ТАКОЕ DOCKER

**Docker** — это система контейнеризации, которая позволяет:
- ✅ Запускать приложение в изолированной среде
- ✅ Гарантировать одинаковую работу на любом компьютере
- ✅ Легко масштабировать и обновлять
- ✅ Развернуть базу данных (PostgreSQL) в одном контейнере с приложением

**Преимущества для GrafikRaboty:**
- 📦 Всё в одном: сервер + база данных + Redis
- 🔄 Лёгкое обновление — пересобрал образ и перезапустил
- 💾 База данных PostgreSQL надёжнее SQLite
- 📱 PWA работает напрямую из Docker

---

## 🚀 БЫСТРЫЙ СТАРТ

### Шаг 1: Проверка Docker

```bash
docker --version
docker-compose --version
```

### Шаг 2: Настройка окружения

```bash
# Скопировать .env.example в .env
copy .env.example .env

# Отредактировать .env (открыть блокнотом)
notepad .env
```

**Заполните в `.env`:**
- `SECRET_KEY` — любой секретный ключ
- `VK_TOKEN` — токен VK группы
- `TELEGRAM_BOT_TOKEN` — токен Telegram бота

### Шаг 3: Запуск Docker

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f web
```

### Шаг 4: Проверка работы

Откройте в браузере:
- **Локально:** http://localhost:8080
- **В сети:** http://192.168.1.207:8080

---

## 🏗️ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Nginx      │  │  Flask Web   │  │  Redis    │ │
│  │   :80/:443   │→ │   :8080      │  │  :6379    │ │
│  │  (reverse)   │  │  (app)       │  │  (cache)  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│         ↓                  ↓                        │
│  ┌──────────────────────────────────────────────┐  │
│  │           PostgreSQL Database                │  │
│  │           :5432                              │  │
│  │  (users, tasks, schedule, sessions, etc.)    │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Volumes:                                            │
│  - postgres_data: База данных                        │
│  - redis_data: Кэш Redis                             │
│  - ./uploads: Файлы пользователей                    │
│  - ./logs: Логи приложения                           │
└─────────────────────────────────────────────────────┘
                      ↓
        ┌─────────────────────────┐
        │   PWA (Android + iOS)   │
        │   + Web Browser         │
        └─────────────────────────┘
```

---

## ⚙️ НАСТРОЙКА ОКРУЖЕНИЯ

### Файл `.env`

| Переменная | Описание | Пример |
|------------|----------|--------|
| `FLASK_ENV` | Режим работы | `production` |
| `SECRET_KEY` | Секретный ключ Flask | `your-secret-key` |
| `POSTGRES_DB` | Имя базы данных | `grafikraboty` |
| `POSTGRES_USER` | Пользователь БД | `grafik` |
| `POSTGRES_PASSWORD` | Пароль БД | `change_this_password` |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram | `8755572729:AAG...` |
| `VK_TOKEN` | Токен VK | `your_vk_token` |
| `VK_GROUP_ID` | ID группы VK | `199112265` |
| `LOCAL_IP` | Локальный IP сервера | `192.168.1.207` |
| `PUBLIC_IP` | Внешний IP сервера | `81.23.181.238` |
| `TUNNEL_URL` | URL туннеля | `https://xxx.loca.lt` |

---

## 🐳 ЗАПУСК В DOCKER

### Обычный запуск (Development)

```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Запуск с PostgreSQL (Production)

```bash
# Запуск всех сервисов включая nginx
docker-compose --profile production up -d --build
```

### Пересборка после изменений

```bash
# Пересобрать и пересоздать контейнеры
docker-compose up -d --build --force-recreate
```

### Доступ к контейнерам

```bash
# Войти в контейнер с приложением
docker exec -it grafikraboty_web bash

# Войти в контейнер с БД
docker exec -it grafikraboty_db bash

# PostgreSQL CLI
docker exec -it grafikraboty_db psql -U grafik -d grafikraboty
```

---

## 🔄 МИГРАЦИЯ ДАННЫХ

### Из SQLite в PostgreSQL

**Вариант 1: Автоматическая миграция**

```bash
# 1. Остановить Docker
docker-compose down

# 2. Запустить миграцию
python scripts/migrate_sqlite_to_postgres.py

# 3. Запустить Docker
docker-compose up -d
```

**Вариант 2: Ручная миграция**

```bash
# 1. Экспорт из SQLite
sqlite3 schedule.db ".dump" > backup.sql

# 2. Конвертация в PostgreSQL формат
# (используйте pgloader или ручной скрипт)

# 3. Импорт в PostgreSQL
docker exec -i grafikraboty_db psql -U grafik -d grafikraboty < backup_pg.sql
```

### Проверка миграции

```bash
# Подключиться к PostgreSQL
docker exec -it grafikraboty_db psql -U grafik -d grafikraboty

# Проверить таблицы
\dt

# Проверить данные
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM work_sessions;
SELECT COUNT(*) FROM barcodes;
```

---

## 📱 PWA УСТАНОВКА

### Что такое PWA?

**Progressive Web App (PWA)** — это веб-приложение которое:
- ✅ Устанавливается на телефон как обычное приложение
- ✅ Работает офлайн (частично)
- ✅ Имеет иконку на рабочем столе
- ✅ Отправляет push-уведомления
- ✅ Работает на Android и iOS

### Установка на Android

1. Откройте Chrome на телефоне
2. Перейдите на `http://192.168.1.207:8080`
3. Нажмите меню (⋮) → **"Установить приложение"**
4. Подтвердите установку
5. Иконка появится на рабочем столе

### Установка на iOS

1. Откройте Safari на iPhone
2. Перейдите на `http://192.168.1.207:8080`
3. Нажмите **"Поделиться"** (квадрат со стрелкой)
4. Выберите **"На экран «Домой»"**
5. Подтвердите установку
6. Иконка появится на рабочем столе

### Проверка PWA

Откройте в браузере DevTools (F12) → **Application** → **Manifest**

Должно отображаться:
- Name: ВетГид корпоративный график
- Short name: График
- Start URL: /get-tunnel-link
- Display: standalone

---

## 🔧 PRODUCTION РАЗВЕРТЫВАНИЕ

### С SSL сертификатом (HTTPS)

**1. Получите SSL сертификат:**

```bash
# Let's Encrypt (бесплатно)
certbot certonly --standalone -d your-domain.com
```

**2. Скопируйте сертификаты:**

```bash
copy C:\certs\fullchain.pem nginx\ssl\
copy C:\certs\privkey.pem nginx\ssl\
```

**3. Включите HTTPS в nginx.conf:**

Раскомментируйте блок `server { listen 443 ssl ... }`

**4. Запустите с production профилем:**

```bash
docker-compose --profile production up -d
```

### С доменным именем

**1. Обновите `.env`:**

```env
PUBLIC_IP=your-domain.com
TUNNEL_URL=https://your-domain.com
```

**2. Обновите `nginx.conf`:**

```nginx
server_name your-domain.com;
```

---

## 📋 КОМАНДЫ DOCKER

### Управление контейнерами

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Статус
docker-compose ps

# Логи
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis
```

### Работа с базой данных

```bash
# Бэкап PostgreSQL
docker exec grafikraboty_db pg_dump -U grafik grafikraboty > backup.sql

# Восстановление из бэкапа
docker exec -i grafikraboty_db psql -U grafik -d grafikraboty < backup.sql

# Очистка базы
docker exec -it grafikraboty_db psql -U grafik -d grafikraboty -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### Очистка

```bash
# Удалить все контейнеры
docker-compose down -v

# Удалить образы
docker rmi grafikraboty_web

# Очистить систему
docker system prune -a
```

---

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### Контейнер не запускается

```bash
# Проверить логи
docker-compose logs web

# Проверить конфиг
docker-compose config

# Пересобрать
docker-compose up -d --build --force-recreate
```

### Ошибка подключения к БД

```bash
# Проверить что БД запущена
docker-compose ps db

# Проверить логи БД
docker-compose logs db

# Проверить переменные окружения
docker-compose exec web env | grep POSTGRES
```

### PWA не устанавливается

1. Проверьте что сайт открывается по **HTTPS** (для production)
2. Проверьте `manifest.json`: `http://localhost:8080/static/manifest.json`
3. Проверьте Service Worker: `http://localhost:8080/static/js/sw.js`
4. Очистите кэш браузера

### Socket.IO не подключается

1. Проверьте что Redis запущен: `docker-compose ps redis`
2. Проверьте логи: `docker-compose logs web | grep socket`
3. Убедитесь что nginx пропускает WebSocket

### Ошибка миграции

```bash
# Проверить что SQLite существует
dir schedule.db

# Запустить миграцию вручную
python scripts/migrate_sqlite_to_postgres.py

# Проверить PostgreSQL
docker exec -it grafikraboty_db psql -U grafik -d grafikraboty -c "\dt"
```

---

## 📊 МОНИТОРИНГ

### Health Check

```bash
# Проверка здоровья приложения
curl http://localhost:8080/api/health

# Проверка здоровья БД
docker exec grafikraboty_db pg_isready
```

### Статистика

```bash
# Использование ресурсов
docker stats

# Размер базы данных
docker exec grafikraboty_db psql -U grafik -d grafikraboty -c "SELECT pg_size_pretty(pg_database_size('grafikraboty'));"
```

---

## 🎯 ССЫЛКИ

- **Локальный доступ:** http://localhost:8080
- **Доступ в сети:** http://192.168.1.207:8080
- **Туннель:** https://rotten-hands-run.loca.lt
- **Admin Panel:** http://localhost:8080/admin

---

**Версия:** 4.30  
**Дата:** 31.03.2026  
**Автор:** Сосямба Assistant
