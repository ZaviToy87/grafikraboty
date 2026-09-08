# -*- coding: utf-8 -*-
"""
web_expiry.py — «Сроки: варианты исполнения, претензии, ответственность».
- срок ≤30 дней  → срочная позиция: печать акционного ценника / скидка / на акц. полку / решение админа;
- принят с остатком <4 мес → автоматическая претензия сотруднику (указал/принял поздно, сразу скидка %);
- админ решает претензию: замечание или штраф (сумма уходит в salary_adjustments), сотруднику в VK.
"""
import os, json, sqlite3, datetime
from flask import Blueprint, render_template, session, redirect, request, jsonify

expiry_bp = Blueprint('expiry', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')

CLAIM_THRESHOLD_DAYS = 120  # принят с остатком меньше 4 месяцев → претензия
URGENT_DAYS = 30            # ≤ месяца → срочная рекомендация


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn()
    try:
        cols = [r[1] for r in c.execute('PRAGMA table_info(product_revisions)')]
        if 'promo_tag_printed' not in cols:
            c.execute('ALTER TABLE product_revisions ADD COLUMN promo_tag_printed INTEGER DEFAULT 0')
        c.execute('CREATE TABLE IF NOT EXISTS revision_claims ('
                  'id INTEGER PRIMARY KEY AUTOINCREMENT, revision_id INTEGER, user_id INTEGER, '
                  'full_name TEXT, product_name TEXT, retail_price REAL, quantity INTEGER, '
                  'expiry_date TEXT, created_at TEXT, days_remaining INTEGER, '
                  'immediate_discount INTEGER, reason TEXT, severity INTEGER DEFAULT 1, '
                  "status TEXT DEFAULT 'new', admin_user_id INTEGER, admin_note TEXT, "
                  'decided_at TEXT, fine_amount REAL DEFAULT 0)')
        c.execute('CREATE TABLE IF NOT EXISTS expiry_sent_log ('
                  'log_date TEXT, kind TEXT, user_id INTEGER, '
                  'PRIMARY KEY (log_date, kind, user_id))')
        c.commit()
    finally:
        c.close()


def _users():
    c = _conn()
    try:
        return {r['id']: r for r in c.execute(
            'SELECT id, username, full_name, role FROM users')}
    finally:
        c.close()


def _vk(uid, msg):
    try:
        from company_rules import _vk_ids_by_user, _send_vk_user
        for vk_id in _vk_ids_by_user().get(int(uid), []):
            try:
                _send_vk_user(vk_id, msg)
            except Exception:
                pass
    except Exception:
        pass


def register_intake_claim(revision_id, user_id, full_name, product_name,
                          retail_price, quantity, expiry_date, days_remaining,
                          discount_percent, created_at=None):
    """Авто-претензия: товар принят/указан с остатком срока меньше 4 месяцев."""
    if days_remaining is None or not (0 <= days_remaining < CLAIM_THRESHOLD_DAYS):
        return None
    if quantity is None or quantity <= 0:
        quantity = 1
    reason = ('short_intake_1m' if days_remaining <= 30 else 'short_intake')
    severity = 3 if days_remaining <= 30 else (2 if days_remaining <= 60 else 1)
    value = round(float(retail_price or 0) * int(quantity), 2)
    created = created_at or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c = _conn()
    try:
        old = c.execute('SELECT id FROM revision_claims WHERE revision_id=?',
                        (revision_id,)).fetchone()
        if old:
            return None
        cur = c.execute(
            'INSERT INTO revision_claims (revision_id, user_id, full_name, product_name, '
            'retail_price, quantity, expiry_date, created_at, days_remaining, '
            'immediate_discount, reason, severity) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (revision_id, user_id, full_name, product_name, retail_price, quantity,
             expiry_date, created, days_remaining, discount_percent, reason, severity))
        c.commit()
        cid = cur.lastrowid
    finally:
        c.close()
    disc = f' сразу со скидкой {discount_percent}%' if discount_percent else ''
    msg = (f"⚠️ Претензия #{cid}: «{product_name}» внесена с остатком срока "
           f"{days_remaining} дн. (< 4 мес){disc}.\nПотенциальная сумма: {value} ₽.")
    _vk(user_id, msg)
    # админам тоже
    umap = {}
    try:
        from company_rules import _vk_ids_by_user
        umap = _vk_ids_by_user()
    except Exception:
        pass
    for u in _users().values():
        if u['role'] == 'admin' and u['id'] != user_id:
            for vk_id in umap.get(u['id'], []):
                try:
                    from company_rules import _send_vk_user
                    _send_vk_user(vk_id, msg + '\nРешить: «Сроки → Претензии».')
                except Exception:
                    pass
    return cid


@expiry_bp.route('/expiry')
def expiry_page():
    if 'user_id' not in session:
        return redirect('/login')
    _ensure()
    return render_template('expiry.html')


@expiry_bp.route('/api/expiry/dashboard')
def api_expiry_dashboard():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    _ensure()
    c = _conn()
    me = session['user_id']
    is_admin = session.get('role') == 'admin'
    def val(rows):
        return [dict(r) for r in rows]
    urgent = val(c.execute(
        "SELECT id, product_name, retail_price, quantity, days_remaining, "
        "discount_percent, final_price, expiry_date, user_id, full_name, "
        "promo_tag_printed, created_at FROM product_revisions "
        "WHERE days_remaining >= 0 AND days_remaining <= ? "
        "AND status IN ('active','discount','admin_decision') ORDER BY days_remaining, expiry_date",
        (URGENT_DAYS,)))
    critical = [r for r in urgent if r['days_remaining'] <= 7]
    soon = [r for r in urgent if r['days_remaining'] > 7]
    expired = val(c.execute(
        "SELECT id, product_name, retail_price, quantity, days_remaining, "
        "discount_percent, final_price, expiry_date, user_id, full_name, created_at "
        "FROM product_revisions WHERE days_remaining < 0 AND status IN ('active','admin_decision')"))
    claims = val(c.execute(
        "SELECT * FROM revision_claims ORDER BY "
        "(status='new') DESC, created_at DESC LIMIT 300"))
    # мои претензии/позиции — для сотрудника отдельно
    my_claims = [cl for cl in claims if cl['user_id'] == me] if not is_admin else []
    my_urgent = [r for r in urgent if r['user_id'] == me] if not is_admin else []
    if is_admin:
        by_user = {}
        for cl in claims:
            by_user.setdefault(cl['user_id'], {'name': cl['full_name'] or '—',
                                               'new': 0, 'accepted': 0, 'fine': 0.0,
                                               'loss': 0.0})
            b = by_user[cl['user_id']]
            b['new'] += 1 if cl['status'] == 'new' else 0
            b['accepted'] += 1 if cl['status'] == 'accepted' else 0
            b['fine'] += float(cl['fine_amount'] or 0) if cl['status'] == 'accepted' else 0
            b['loss'] += round((float(cl['retail_price'] or 0)) * int(cl['quantity'] or 1), 2)
        by_user = [dict({'user_id': k}, **v) for k, v in by_user.items()]
    else:
        by_user = []

    def total(rows, key_loss=None):
        return round(sum((float(r['retail_price'] or 0) * int(r['quantity'] or 1))
                         for r in rows), 2)

    c.close()
    return jsonify({'status': 'success', 'is_admin': is_admin,
                    'urgent': urgent, 'critical': critical, 'soon': soon,
                    'expired': expired, 'claims': claims,
                    'my_claims': my_claims, 'my_urgent': my_urgent,
                    'by_user': by_user,
                    'loss_critical': total(critical), 'loss_soon': total(soon),
                    'loss_expired': total(expired)})


@expiry_bp.route('/api/expiry/variant/<int:rid>', methods=['POST'])
def api_expiry_variant(rid):
    """Вариант исполнения по позиции (срок подходит)."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    data = request.json or {}
    variant = data.get('variant')
    allowed = {'promo_tag', 'apply_discount', 'write_off', 'ask_admin', 'resolved'}
    if variant not in allowed:
        return jsonify({'status': 'error', 'message': 'Некорректный вариант'}), 400
    _ensure()
    c = _conn()
    row = c.execute('SELECT * FROM product_revisions WHERE id=?', (rid,)).fetchone()
    if not row:
        c.close()
        return jsonify({'status': 'error', 'message': 'Позиция не найдена'}), 404
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_status = None
    note = None
    if variant == 'apply_discount':
        try:
            d = float(data.get('discount', 0))
        except Exception:
            d = 0
        d = max(0, min(80, d))
        fp = round(float(row['retail_price']) * (1 - d / 100), 2)
        c.execute('UPDATE product_revisions SET discount_percent=?, final_price=?, '
                  'status=?, updated_at=? WHERE id=?',
                  (d, fp, 'discount', now, rid))
        note = f'Скидка {d}%, цена {fp}'
    elif variant == 'promo_tag':
        c.execute('UPDATE product_revisions SET promo_tag_printed=1, status=?, '
                  "updated_at=? WHERE id=?", ('discount', now, rid))
        note = 'Отмечено: акционный ценник распечатан'
    elif variant == 'write_off':
        c.execute("UPDATE product_revisions SET status='written_off_expired', quantity=0, "
                  'updated_at=? WHERE id=?', (now, rid))
        note = 'Списано по сроку'
    elif variant == 'ask_admin':
        c.execute("UPDATE product_revisions SET status='admin_decision', updated_at=? "
                  'WHERE id=?', (now, rid))
        note = 'Отправлено на решение администратора'
    elif variant == 'resolved':
        c.execute("UPDATE product_revisions SET status='discount', updated_at=? "
                  'WHERE id=?', (now, rid))
        note = 'Отмечено как выполненное'
    c.commit()
    # аудит
    try:
        c.execute('INSERT INTO revision_audit_log (revision_id, user_id, full_name, '
                  'action, new_value) VALUES (?,?,?,?,?)',
                  (rid, session['user_id'], session.get('full_name') or session.get('username'),
                   'expiry_variant_' + variant, json.dumps({'note': note}, ensure_ascii=False)))
        c.commit()
    except Exception:
        pass
    c.close()
    return jsonify({'status': 'success', 'message': note or 'Выполнено',
                    'print_url': ('/expiry/tags?id=' + str(rid)) if variant == 'promo_tag' else None})


@expiry_bp.route('/api/expiry/claims/<int:cid>/resolve', methods=['POST'])
def api_claim_resolve(cid):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Только администратор'}), 403
    data = request.json or {}
    decision = data.get('decision')
    fine = 0.0
    try:
        fine = round(float(data.get('fine', 0) or 0), 2)
    except Exception:
        fine = 0.0
    note = (data.get('note') or '').strip()[:500]
    _ensure()
    c = _conn()
    row = c.execute('SELECT * FROM revision_claims WHERE id=?', (cid,)).fetchone()
    if not row:
        c.close()
        return jsonify({'status': 'error', 'message': 'Претензия не найдена'}), 404
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = 'accepted' if decision == 'accept' else 'dismissed'
    if decision != 'accept':
        fine = 0.0
    c.execute('UPDATE revision_claims SET status=?, admin_user_id=?, admin_note=?, '
              'decided_at=?, fine_amount=? WHERE id=?',
              (status, session['user_id'], note, now, fine, cid))
    if decision == 'accept' and fine > 0:
        try:
            year = datetime.date.today().year
            month = datetime.date.today().month
            c.execute('INSERT INTO salary_adjustments '
                      '(user_id, year, month, amount, reason, created_by, created_at) '
                      'VALUES (?,?,?,?,?,?,?)',
                      (row['user_id'], year, month, -fine,
                       'Штраф: претензия по сроку — ' + (row['product_name'] or ''),
                       session['user_id'], now))
        except Exception:
            pass
    c.commit()
    c.close()
    verdict = ('принята (штраф %.0f ₽)' % fine) if fine > 0 else \
        ('принята как замечание' if decision == 'accept' else 'отклонена')
    _vk(row['user_id'],
        f"⚖️ По претензии #{cid} «{row['product_name']}» решение: {verdict}."
        + (('\nКомментарий: ' + note) if note else ''))
    return jsonify({'status': 'success', 'message': f'Претензия #{cid} {verdict}'})


@expiry_bp.route('/expiry/tags')
def expiry_tags_print():
    """Печатные акционные ценники для выбранных позиций."""
    if 'user_id' not in session:
        return redirect('/login')
    ids = [int(x) for x in (request.args.get('id') or '').split(',')
           if x.strip().isdigit()]
    rows = []
    if ids:
        _ensure()
        c = _conn()
        q = ('SELECT product_name, retail_price, discount_percent, final_price, '
             'quantity, expiry_date, barcode FROM product_revisions WHERE id IN (%s)'
             % ','.join('?' * len(ids)))
        rows = [dict(r) for r in c.execute(q, ids)]
        c.close()
    return render_template('expiry_tags.html', rows=rows)


def send_expiry_digest(force=False):
    """Ежедневная рассылка по срокам: лично ответственному, админу — сводка."""
    try:
        _ensure()
        c = _conn()
        today = datetime.date.today().isoformat()
        urgent = [dict(r) for r in c.execute(
            "SELECT id, product_name, retail_price, quantity, days_remaining, "
            "discount_percent, final_price, user_id, full_name, created_at "
            "FROM product_revisions WHERE days_remaining >= 0 AND days_remaining <= ? "
            "AND status IN ('active','discount','admin_decision') "
            "ORDER BY days_remaining, expiry_date", (URGENT_DAYS,))]
        new_claims = [dict(r) for r in c.execute(
            "SELECT * FROM revision_claims WHERE status='new' ORDER BY created_at")]
        c.close()
        if not urgent and not new_claims:
            return 0
        by_user = {}
        for r in urgent:
            by_user.setdefault(r['user_id'], []).append(r)
        sent = 0
        c = _conn()
        try:
            for uid, items in by_user.items():
                if not force and _sent(c, (today, 'urgent', uid)):
                    continue
                val = sum(float(x['retail_price'] or 0) * int(x['quantity'] or 1)
                          for x in items)
                lines = ['🔔 СРОЧНО: подходят сроки (до 30 дней)!', '',
                         f"Позиций: {len(items)}, сумма по рознице: {round(val, 0):.0f} ₽"]
                for x in items[:10]:
                    lines.append(f"• {x['product_name']} — {x['days_remaining']} дн., "
                                 f"скидка {x['discount_percent']}% "
                                 f"(цена {x['final_price']} ₽)")
                if len(items) > 10:
                    lines.append(f"… и ещё {len(items) - 10}")
                lines += ['', 'Что делать: распечатать акционный ценник / скидка / '
                          'акционная полка. Раздел: «Сроки → Срочные».']
                _vk(uid, '\n'.join(lines))
                _mark(c, (today, 'urgent', uid))
                sent += 1
            users = _users()
            for u in users.values():
                if u['role'] != 'admin':
                    continue
                if not force and _sent(c, (today, 'summary', u['id'])):
                    continue
                loss = sum(float(x['retail_price'] or 0) * int(x['quantity'] or 1)
                           for x in urgent)
                my_urgent = [r for r in urgent if r['user_id'] == u['id']]
                msg = (f"📅 Сроки на {today}:\n"
                       f"• срочных позиций (≤30 дн.): {len(urgent)} "
                       f"— риск {loss:.0f} ₽\n"
                       f"• открытых претензий: {len(new_claims)}\n"
                       f"• из них ваших срочных: {len(my_urgent)}\n"
                       f"Раздел: «Сроки → Претензии».")
                _vk(u['id'], msg)
                _mark(c, (today, 'summary', u['id']))
                sent += 1
        finally:
            c.close()
        return sent
    except Exception as e:
        try:
            import logging
            logging.getLogger('web_expiry').warning('digest error: %s' % e)
        except Exception:
            pass
        return 0


def _sent(c, key):
    try:
        return c.execute('SELECT 1 FROM expiry_sent_log WHERE log_date=? '
                         'AND kind=? AND user_id=?', key).fetchone() is not None
    except Exception:
        return False


def _mark(c, key):
    try:
        c.execute('INSERT OR IGNORE INTO expiry_sent_log (log_date, kind, user_id) '
                  'VALUES (?,?,?)', key)
        c.commit()
    except Exception:
        pass


def start_expiry_scheduler():
    import schedule as _schedule
    import threading as _th
    import time as _t

    def loop():
        while True:
            _schedule.run_pending()
            _t.sleep(60)

    try:
        send_expiry_digest(force=True)
    except Exception:
        pass
    try:
        _schedule.every().day.at('09:20').do(send_expiry_digest)
    except Exception:
        pass
    th = _th.Thread(target=loop, daemon=True)
    th.start()
    return th

