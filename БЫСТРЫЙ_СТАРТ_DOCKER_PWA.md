# 🚀 БЫСТРЫЙ СТАРТ DOCKER + PWA
## GrafikRaboty v4.30

---

## ⚡ 5 МИНУТ ДО ЗАПУСКА

### Шаг 1: Проверка Docker

Откройте командную строку:

```bash
docker --version
docker-compose --version
```

Если не установлено — скачайте с https://docker.com/products/docker-desktop

---

### Шаг 2: Настройка .env

Файл `.env` уже создан с вашими настройками!

**Проверьте что заполнено:**
- ✅ `TELEGRAM_BOT_TOKEN` — уже стоит ваш токен
- ✅ `LOCAL_IP` — 192.168.1.207
- ✅ `PUBLIC_IP` — 81.23.181.238
- ✅ `VK_GROUP_ID` — 199112265

**Нужно изменить:**
- 🔧 `SECRET_KEY` — придумайте любой секрет
- 🔧 `VK_TOKEN` — вставьте токен VK группы
- 🔧 `POSTGRES_PASSWORD` — смените пароль БД

---

### Шаг 3: Запуск Docker

```bash
# Перейдите в папку проекта
cd C:\Users\User\Desktop\GrafikRaboty

# Запустите Docker (сборка + запуск)
docker-compose up -d --build

# Ждите 1-2 минуты...
```

---

### Шаг 4: Проверка

```bash
# Статус контейнеров
docker-compose ps

# Должно быть 3 контейнера:
# - grafikraboty_web (зелёный)
# - grafikraboty_db (зелёный)
# - grafikraboty_redis (зелёный)
```

---

### Шаг 5: Откройте приложение

**Варианты доступа:**

| Способ | Ссылка | Когда использовать |
|--------|--------|-------------------|
| **Локально** | http://localhost:8080 | На этом компьютере |
| **В сети** | http://192.168.1.207:8080 | С других устройств в Wi-Fi |
| **Через туннель** | https://xxx.loca.lt | Из интернета |

---

## 📱 УСТАНОВКА НА ТЕЛЕФОН (PWA)

### Android

1. Откройте **Chrome** на телефоне
2. Перейдите на `http://192.168.1.207:8080`
3. Нажмите **⋮ (меню)** → **"Установить приложение"**
4. Готово! Иконка на рабочем столе

### iOS (iPhone)

1. Откройте **Safari** на iPhone
2. Перейдите на `http://192.168.1.207:8080`
3. Нажмите **"Поделиться"** → **"На экран «Домой»"**
4. Готово! Иконка на рабочем столе

---

## 🔧 УПРАВЛЕНИЕ

### Остановить

```bash
docker-compose down
```

### Перезапустить

```bash
docker-compose restart
```

### Посмотреть логи

```bash
# Все логи
docker-compose logs -f

# Только веб-сервер
docker-compose logs -f web

# Только база данных
docker-compose logs -f db
```

### Обновить после изменений кода

```bash
# Пересобрать и перезапустить
docker-compose up -d --build --force-recreate
```

---

## 📊 МОНИТОРИНГ

### Проверка здоровья

```bash
# API health check
curl http://localhost:8080/api/health

# Должно вернуть: {"status": "ok"}
```

### Статус контейнеров

```bash
docker stats
```

### Размер базы данных

```bash
docker exec grafikraboty_db psql -U grafik -d grafikraboty -c "SELECT pg_size_pretty(pg_database_size('grafikraboty'));"
```

---

## 🐛 ПРОБЛЕМЫ

### Контейнер не запускается

```bash
# Посмотреть логи
docker-compose logs web

# Исправить ошибку и пересобрать
docker-compose up -d --build
```

### Ошибка подключения к БД

```bash
# Проверить что БД запущена
docker-compose ps db

# Перезапустить БД
docker-compose restart db
```

### PWA не устанавливается

1. Откройте http://localhost:8080 в Chrome
2. Нажмите F12 → Application → Manifest
3. Проверьте что нет ошибок
4. Очистите кэш браузера

---

## 📋 ССЫЛКИ

- **Dashboard:** http://localhost:8080
- **Admin Panel:** http://localhost:8080/admin
- **Chat:** http://localhost:8080/chat
- **API Health:** http://localhost:8080/api/health

---

## 🎯 ЧТО ДАЛЬШЕ?

1. ✅ Проверьте что приложение открывается
2. ✅ Установите PWA на телефон
3. ✅ Протестируйте сканер штрих-кодов
4. ✅ Проверьте чат и уведомления

---

**Готово!** 🎉

Приложение работает в Docker, доступно по сети и устанавливается на телефоны!

---

**Версия:** 4.30  
**Дата:** 31.03.2026  
**Сосямба Assistant**
