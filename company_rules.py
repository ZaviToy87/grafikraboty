# -*- coding: utf-8 -*-
"""
company_rules.py — Правила магазина и Методичка сотрудника.

* Хранит документы (Правила, Методичка) в БД (таблица company_docs) и
  загружает их тексты из папки docs/, чтобы сотрудники всегда могли
  прочитать в программе (страница /rules).
* Ежедневно (по графику смен) напоминает сотрудникам, кто работает в этот
  день, о задачах смены и необходимости свериться с правилами/методичкой.
  Отправка: в Telegram (группа + лично, по telegram_user_map из
  telegram_config.json) и во внутренние уведомления программы.
"""
import os
import io
import re
import json
import sqlite3
import threading
import schedule
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
try:
    from app_paths import DB_PATH, DATA_DIR
except Exception:
    DB_PATH = os.path.join(BASE_DIR, 'schedule.db')
    DATA_DIR = BASE_DIR

DOCS_DIR = os.path.join(BASE_DIR, 'docs')

REPEAT_TASKS = [
    # (task_name_keywords, описание/совет из методички)
    ('ценник', 'Проверь ценники и сроки годности на полках — методичка: '
               'сроки до 4 мес → скидка 10%, 3 мес → 15%, 2 мес → 20%, '
               '1 мес → 25–50% (по маржинальности).'),
    ('срок', 'Проверь сроки годности товаров — товары с подходящим сроком '
             'вынеси на акцию по схеме из методички.'),
    ('уборк', 'Поддерживай чистоту: полки, пол, приёмка — по правилам '
              '«Правила магазина».'),
    ('протир', 'Влажная уборка полок по «Правилам магазина» (не мокрой '
               'тряпкой, перенеси товар, дай высохнуть).'),
    ('ревиз', 'Сегодня ревизия — сверь остатки, аккуратно переноси товары '
              'двумя руками.'),
    ('акци', 'Вынеси товары с подходящими сроками на акции (схема скидок '
             'в методичке).'),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(db=None):
    db = db or get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS company_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            filename TEXT,
            body TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()


def _load_text_files():
    """Читает тексты документов из папки docs."""
    result = []
    if not os.path.isdir(DOCS_DIR):
        return result
    for fn in sorted(os.listdir(DOCS_DIR)):
        if not fn.lower().endswith('.txt'):
            continue
        path = os.path.join(DOCS_DIR, fn)
        try:
            with io.open(path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception:
            continue
        low = fn.lower()
        if 'правил' in low:
            title, cat = 'Правила магазина', 'Обязанности и порядок'
        elif 'методичк' in low:
            title, cat = 'Методичка и должностные обязанности', 'Методичка'
        else:
            title, cat = fn.replace('.txt', ''), 'Документы'
        result.append({'title': title, 'category': cat,
                       'filename': fn, 'body': text})
    return result


def seed_docs(db=None):
    """Добавляет документы из docs/ в БД, если их там ещё нет."""
    db = db or get_db()
    ensure_table(db)
    for doc in _load_text_files():
        cur = db.execute('SELECT COUNT(*) AS n FROM company_docs '
                         'WHERE title = ?', (doc['title'],))
        if cur.fetchone()['n'] == 0:
            db.execute(
                'INSERT INTO company_docs (title, category, filename, body) '
                'VALUES (?, ?, ?, ?)',
                (doc['title'], doc['category'], doc['filename'], doc['body']))
    db.commit()
    return len(_load_text_files())


def get_docs(db=None):
    db = db or get_db()
    ensure_table(db)
    rows = db.execute('SELECT id, title, category, filename, body, updated_at '
                      'FROM company_docs ORDER BY id').fetchall()
    return [dict(r) for r in rows]


# ============================================================
# Напоминания по графику смен
# ============================================================
def _load_tg():
    try:
        path = os.path.join(DATA_DIR, 'telegram_config.json')
        with io.open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        token = cfg.get('bot_token') or cfg.get('token') or ''
        group = [str(x) for x in (cfg.get('chat_ids') or [])]
        user_map = cfg.get('telegram_user_map') or {}
        user_to_chat = {}
        for cid, uid in user_map.items():
            user_to_chat.setdefault(str(uid), []).append(str(cid))
        return {'token': token, 'group': group, 'users': user_to_chat,
                'time': cfg.get('rules_reminder_time', '08:40')}
    except Exception as e:
        return {'token': '', 'group': [], 'users': {}, 'time': '08:40'}


def _vk_config():
    """Загружает vk_config.json (service_token, vk_user_map)."""
    cfg = {}
    for folder in (DATA_DIR, BASE_DIR):
        try:
            with io.open(os.path.join(folder, 'vk_config.json'),
                         'r', encoding='utf-8') as f:
                cfg = json.load(f)
            if cfg.get('service_token'):
                break
        except Exception:
            continue
    return cfg


def _vk_ids_by_user():
    """user_id системы -> список его VK ID (из vk_user_map)."""
    cfg = _vk_config()
    umap = cfg.get('vk_user_map') or {}
    result = {}
    for vk_id, uid in umap.items():
        result.setdefault(int(uid), []).append(int(vk_id))
    return result


def _send_vk_user(vk_id, text):
    """Отправляет личное сообщение пользователю ВК через сообщество."""
    if not vk_id:
        return False
    cfg = _vk_config()
    token = cfg.get('service_token') or ''
    if not token:
        return False
    try:
        import urllib.request
        import urllib.parse
        import json as _json
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        params = urllib.parse.urlencode({
            'peer_id': int(vk_id),
            'message': text,
            'random_id': int(__import__('time').time() * 1000),
            'access_token': token,
            'v': '5.131',
        }).encode('utf-8')
        url = 'https://api.vk.com/method/messages.send'
        req = urllib.request.Request(url, data=params)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = _json.loads(resp.read().decode('utf-8', 'replace'))
            return bool(data.get('response'))
    except Exception as e:
        try:
            import logging
            logging.getLogger('company_rules').warning(
                'VK send to %s failed: %s' % (vk_id, e))
        except Exception:
            pass
        return False



def _today_tasks(db, d):
    """Задачи на дату d: по графику сотрудников + повторяющиеся по числам."""
    from web_config import send_telegram_message  # noqa: F401 (просто импорт гарантирует зависимости)
    tasks_map = {}
    try:
        for r in db.execute('SELECT id, name FROM tasks'):
            tasks_map[r['id']] = r['name']
    except Exception:
        pass
    result = {}
    try:
        rows = db.execute('SELECT user_id, task_ids FROM work_schedule '
                          'WHERE year=? AND month=? AND day=?',
                          (d.year, d.month, d.day)).fetchall()
    except Exception:
        rows = []
    for r in rows:
        uid = r['user_id']
        names = []
        for tid in re.split(r'[,\s]+', (r['task_ids'] or '')):
            if tid.isdigit() and int(tid) in tasks_map:
                names.append(tasks_map[int(tid)])
        result.setdefault(uid, [])
        result[uid].extend(names)
    # те, кто уже открыл смену сегодня (касса), тоже работают
    try:
        sess = db.execute('SELECT DISTINCT user_id FROM work_sessions '
                          'WHERE year=? AND month=? AND day=?',
                          (d.year, d.month, d.day)).fetchall()
        for r in sess:
            result.setdefault(r['user_id'], [])
    except Exception:
        pass
    # повторяющиеся задачи по числам/дням недели
    try:
        from recurring_schedule import RECURRING_TASKS
    except Exception:
        RECURRING_TASKS = []
    for t in RECURRING_TASKS:
        due = False
        st = t.get('schedule_type')
        if st == 'weekly' and t.get('weekday') == d.weekday():
            due = True
        elif st == 'monthly_days' and d.day in (t.get('days') or []):
            due = True
        if due:
            # повторяющиеся задачи добавляем всем работающим сегодня
            for uid in list(result.keys()):
                if t['name'] not in result[uid]:
                    result[uid].append(t['name'])
    return result


def _tips_for(task_names):
    tips = []
    for name in task_names:
        low = (name or '').lower()
        short = ''
        for kw, tip in REPEAT_TASKS:
            if kw in low:
                short = tip
                break
        detail = _task_guidance(low)
        if short and not detail:
            tips.append('• %s: %s' % (name, short))
        elif detail:
            tips.append('• %s — %s\n%s' % (name, short or 'инструкция:',
                                            detail))
        elif low:
            pass
    return tips


_docs_cache = {}


def _load_docs():
    if not _docs_cache:
        for key, fn in (('rules', 'Правила_магазина.txt'),
                        ('method', 'МЕТОДИЧКА_сотрудника.txt')):
            try:
                with io.open(os.path.join(DOCS_DIR, fn), 'r',
                             encoding='utf-8') as f:
                    _docs_cache[key] = f.read().splitlines()
            except Exception:
                _docs_cache[key] = []
    return _docs_cache


def _task_guidance(low, max_chars=1700):
    """Ищет в Правилах/Методичке раздел, подходящий задаче, и возвращает текст."""
    import re as _re
    # тема раздела по ключевым словам задачи
    theme = None
    for kw, theme_key in [
        ('полк', 'полк'), ('протир', 'полк'), ('уборк', 'полк'),
        ('мусор', 'мусор'), ('сануз', 'унитаз'), ('унитаз', 'унитаз'),
        ('чайник', 'чайник'), ('микроволн', 'микроволн'),
        ('холодильн', 'холодильник'), ('посуд', 'посуд'),
        ('развеш', 'развешивать корм'), ('корм', 'развешивать корм'),
        ('ценник', 'ценник'), ('срок', 'срок'), ('акци', 'акци'),
        ('ревиз', 'ревизи'), ('приемк', 'приемк'),
    ]:
        if kw in low:
            theme = theme_key
            break
    if not theme:
        return ''
    rules = _load_docs()['rules']
    method = _load_docs()['method']
    # сначала Правила магазина, потом Методичка
    for lines in (rules, method):
        started = False
        buf = []
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if _re.match(r'^\s*\d+\.', s) or _re.match(r'^(К[А-Я]К|ПРАВИЛ|МЕТОД)', s):
                if started:
                    break
                if theme in s.lower():
                    started = True
                    buf.append(s)
                    continue
                continue
            if started:
                if '……' in s or _re.match(r'^_{6,}', s):
                    break
                buf.append(s)
            if len('\n'.join(buf)) > max_chars:
                break
        if len(buf) >= 3:
            return '\n'.join(buf[:60])
    return ''


def _ensure_state_and_notif(db):
    db.execute('''
        CREATE TABLE IF NOT EXISTS rules_state (
            key TEXT PRIMARY KEY, value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, type TEXT, title TEXT, message TEXT,
            link TEXT, is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    db.commit()


def _already_sent(db, key):
    row = db.execute('SELECT value FROM rules_state WHERE key = ?',
                     (key,)).fetchone()
    return bool(row and row['value'] == '1')


def _mark_sent(db, key):
    db.execute('INSERT OR REPLACE INTO rules_state (key, value) VALUES (?, ?)',
               (key, '1'))
    db.commit()


def _fmt_date(d):
    return d.strftime('%d.%m.%Y')


def send_today_shift_reminder(force=False):
    """
    Отправляет напоминания о смене и задачах всем, кто работает сегодня.

    Канал: Telegram (группа + лично) и внутренние уведомления.
    Возвращает количество отправленных Telegram-сообщений.
    """
    db = get_db()
    ensure_table(db)
    _ensure_state_and_notif(db)
    d = date.today()
    key = 'remind_%s' % d.isoformat()
    if not force and _already_sent(db, key):
        return 0

    tg = _load_tg()
    vk_ids_by_user = _vk_ids_by_user()
    users_tasks = _today_tasks(db, d)
    if not users_tasks:
        db.close()
        return 0

    # имена пользователей
    unames = {}
    for r in db.execute('SELECT id, username, full_name FROM users'):
        unames[r['id']] = r['full_name'] or r['username']

    try:
        from web_config import send_telegram_message
    except Exception:
        send_telegram_message = None

    sent = 0
    for uid, tasks in sorted(users_tasks.items()):
        name = unames.get(uid, 'Сотрудник')
        tips = _tips_for(tasks)
        lines = ['📋 Напоминание на %s' % _fmt_date(d), '']
        lines.append('👤 %s — сегодня твоя смена.' % name)
        lines.append('Задачи: %s' % (', '.join(tasks)
                                     if tasks else 'работа по графику'))
        if tips:
            lines.append('')
            lines.append('📌 Не забудь:')
            lines.extend(tips)
        lines.append('')
        lines.append('📖 Правила магазина и методичка — в программе, '
                     'раздел «📖 Правила и методичка».')
        msg = '\n'.join(lines)

        # Личное сообщение в ВК (основной канал)
        delivered = False
        for vk_id in vk_ids_by_user.get(uid, []):
            if _send_vk_user(vk_id, msg):
                sent += 1
                delivered = True
        # Если для сотрудника нет VK — пробуем Telegram
        if not delivered and send_telegram_message:
            for cid in (tg.get('users') or {}).get(str(uid), []):
                try:
                    s, _ = send_telegram_message([cid], msg,
                                                 token=tg.get('token', ''))
                    sent += s
                    delivered = True
                    break
                except Exception:
                    pass

        # Внутреннее уведомление в программе
        try:
            db.execute('INSERT INTO notifications (user_id, type, title, '
                       'message, link) VALUES (?, ?, ?, ?, ?)',
                       (uid, 'rule_reminder', 'Напоминание о смене %s'
                        % _fmt_date(d), msg, '/rules'))
        except Exception:
            pass
    db.commit()

    _mark_sent(db, key)
    db.close()
    return sent


def _scheduler_loop():
    import time as _t
    while True:
        schedule.run_pending()
        _t.sleep(60)


def start_rules_scheduler():
    """Запускает ежедневные напоминания в фоновом потоке."""
    try:
        send_today_shift_reminder(force=False)  # сразу за сегодня
    except Exception as e:
        try:
            import logging
            logging.getLogger('company_rules').warning(
                'rules remind now failed: %s' % e)
        except Exception:
            pass
    tg = _load_tg()
    try:
        schedule.every().day.at(tg.get('time', '08:40')).do(
            send_today_shift_reminder)
    except Exception:
        try:
            schedule.every().day.at('08:40').do(send_today_shift_reminder)
        except Exception:
            pass
    th = threading.Thread(target=_scheduler_loop, daemon=True)
    th.start()
    return th


