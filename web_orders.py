# -*- coding: utf-8 -*-
"""web_orders.py — «Заявки на заказ»: остатки 1С + продажи → рекомендации и заявка с VK."""
import os, json, math, sqlite3, datetime, re
from flask import Blueprint, render_template, session, redirect, request, jsonify

orders_bp = Blueprint('orders', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure_tables():
    c = _conn()
    try:
        cols = [r[1] for r in c.execute('PRAGMA table_info(products_1c)')]
        if 'quantity' not in cols:
            c.execute('ALTER TABLE products_1c ADD COLUMN quantity REAL')
        c.execute('CREATE TABLE IF NOT EXISTS purchase_orders ('
                  'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                  'created_by INTEGER, created_at TEXT, status TEXT DEFAULT \'new\','
                  'note TEXT, items_json TEXT, decided_by INTEGER, decided_at TEXT)')
        c.commit()
    finally:
        c.close()


def _norm(name):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\sа-яё0-9]', '',
                                       str(name or '').strip().lower())) if name else ''


def _notify_admins(title, message):
    umap = {}
    try:
        from company_rules import _vk_ids_by_user, _send_vk_user
        umap = _vk_ids_by_user()
    except Exception:
        pass
    try:
        c = _conn()
        for uid in [r['id'] for r in c.execute(
                "SELECT id FROM users WHERE role='admin'")]:
            try:
                c.execute('INSERT INTO notifications (user_id,type,title,message,link) '
                          'VALUES (?,?,?,?,?)', (uid, 'order_request', title, message, '/orders'))
            except Exception:
                pass
            for vk_id in umap.get(uid, []):
                try:
                    _send_vk_user(vk_id, message)
                except Exception:
                    pass
        c.commit()
        c.close()
    except Exception:
        pass


@orders_bp.route('/orders')
def orders_page():
    if 'user_id' not in session:
        return redirect('/login')
    _ensure_tables()
    return render_template('orders.html')


@orders_bp.route('/api/orders/recommendations')
def api_recommendations():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    days = max(1, min(90, request.args.get('days', 7, type=int)))
    stale_days = max(30, min(365, request.args.get('stale_days', 60, type=int)))
    _ensure_tables()
    c = _conn()
    ref = None
    row = c.execute('SELECT MAX(date) AS m FROM sync_sales').fetchone()
    if row and row['m']:
        try:
            ref = datetime.date.fromisoformat(str(row['m'])[:10])
        except Exception:
            ref = None
    ref = ref or datetime.date.today()
    since = (ref - datetime.timedelta(days=days)).isoformat()
    since_stale = (ref - datetime.timedelta(days=stale_days)).isoformat()
    sql = ('SELECT si.nomenclature_name n, ROUND(SUM(si.quantity),2) q, '
           'COUNT(*) cnt, ROUND(SUM(si.sum),2) s FROM sync_sale_items si '
           'JOIN sync_sales ss ON ss.guid=si.sale_guid WHERE ss.date >= ? '
           'GROUP BY si.nomenclature_name')
    short, wide = {}, {}
    for r in c.execute(sql, (since,)):
        short[_norm(r['n'])] = (float(r['q'] or 0), int(r['cnt']), float(r['s'] or 0))
    for r in c.execute(sql, (since_stale,)):
        wide[_norm(r['n'])] = float(r['q'] or 0)
    prods = [dict(r) for r in c.execute(
        'SELECT id, name, full_name, retail_price, purchase_price, quantity, '
        'barcode_main, group_name, unit FROM products_1c WHERE is_active != 0')]
    c.close()

    to_order, stale, stock_known = [], [], 0
    for p in prods:
        s7 = None
        for a in (_norm(p.get('name')), _norm(p.get('full_name'))):
            if a and a in short:
                s7 = short[a]
                break
        qty = p.get('quantity')
        if qty is not None:
            try:
                qty = float(qty)
                stock_known += 1
            except Exception:
                qty = None
        if s7 and s7[0] > 0:
            sell, cnt, ssum = s7
            suggested = int(math.ceil(sell))
            if qty is not None and qty > 0 and qty >= sell:
                suggested = 0
            elif qty is not None and qty > 0:
                suggested = max(1, int(math.ceil(sell - qty)))
            to_order.append({'product_id': p['id'],
                             'name': p.get('full_name') or p.get('name'),
                             'group': p.get('group_name') or '',
                             'retail': p.get('retail_price'),
                             'purchase': p.get('purchase_price'),
                             'quantity': qty, 'sold7': round(sell, 1),
                             'sales7_sum': round(ssum, 2),
                             'suggested': suggested,
                             'unit': p.get('unit') or ''})
        elif qty is not None and qty > 0:
            w = None
            for a in (_norm(p.get('name')), _norm(p.get('full_name'))):
                if a and a in wide:
                    w = wide[a]
                    break
            if not w or w <= 0:
                stale.append({'product_id': p['id'],
                              'name': p.get('full_name') or p.get('name'),
                              'group': p.get('group_name') or '',
                              'retail': p.get('retail_price'),
                              'quantity': qty,
                              'days_no_sale': stale_days,
                              'unit': p.get('unit') or ''})
    to_order.sort(key=lambda x: x['sold7'], reverse=True)
    stale.sort(key=lambda x: x['quantity'], reverse=True)
    return jsonify({'status': 'success', 'ref_date': ref.isoformat(),
                    'window_days': days, 'stale_days': stale_days,
                    'stock_known': stock_known,
                    'to_order': to_order[:150], 'stale': stale[:150]})


@orders_bp.route('/api/orders/create', methods=['POST'])
def api_order_create():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    data = request.json or {}
    clean = []
    for it in (data.get('items') or []):
        try:
            name = (it.get('name') or '').strip()
            qty = float(it.get('qty', it.get('suggested', 1)) or 1)
            if name and qty > 0:
                clean.append({'product_id': it.get('product_id'),
                              'name': name[:300], 'qty': round(qty, 3),
                              'price': it.get('price')})
        except Exception:
            continue
    if not clean:
        return jsonify({'status': 'error', 'message': 'Добавьте позиции в заявку'}), 400
    _ensure_tables()
    c = _conn()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = c.execute('INSERT INTO purchase_orders (created_by, created_at, status, '
                    'note, items_json) VALUES (?,?,?,?,?)',
                    (session['user_id'], now, 'new',
                     (data.get('note') or '')[:500],
                     json.dumps(clean, ensure_ascii=False)))
    c.commit()
    oid = cur.lastrowid
    me = session.get('full_name') or session.get('username') or 'Сотрудник'
    lines = '\n'.join(f"• {x['name']} — {x['qty']}" for x in clean[:8])
    if len(clean) > 8:
        lines += f"\n… и ещё {len(clean) - 8}"
    _notify_admins('Заявка на заказ #%s' % oid,
                   f"🛒 Заявка #{oid} от {me}\n\n{lines}\n\nОткрыть: «Заявки на заказ»")
    return jsonify({'status': 'success', 'id': oid,
                    'message': f'Заявка #{oid} создана и отправлена руководителю'})


@orders_bp.route('/api/orders/list')
def api_orders_list():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    _ensure_tables()
    c = _conn()
    if session.get('role') == 'admin':
        rows = c.execute('SELECT * FROM purchase_orders ORDER BY id DESC LIMIT 200')
    else:
        rows = c.execute('SELECT * FROM purchase_orders WHERE created_by=? '
                         'ORDER BY id DESC LIMIT 100', (session['user_id'],))
    out = []
    for r in rows:
        d = dict(r)
        try:
            d['items'] = json.loads(d.get('items_json') or '[]')
        except Exception:
            d['items'] = []
        d.pop('items_json', None)
        out.append(d)
    c.close()
    uids = {o.get('created_by') for o in out}
    names = {}
    if uids:
        c = _conn()
        try:
            names = {r['id']: (r['full_name'] or r['username']) for r in c.execute(
                'SELECT id, full_name, username FROM users WHERE id IN (%s)'
                % ','.join('?' * len(uids)), tuple(uids))}
        except Exception:
            pass
        c.close()
    for o in out:
        o['author'] = names.get(o.get('created_by')) or '—'
    return jsonify({'status': 'success', 'orders': out})


@orders_bp.route('/api/orders/<int:oid>/status', methods=['POST'])
def api_order_status(oid):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 401
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Только для администратора'}), 403
    status = (request.json or {}).get('status', '')
    if status not in ('approved', 'ordered', 'rejected', 'new'):
        return jsonify({'status': 'error', 'message': 'Некорректный статус'}), 400
    labels = {'approved': '✅ одобрена', 'ordered': '🛒 заказана',
              'rejected': '❌ отклонена', 'new': '🔄 возвращена в работу'}
    _ensure_tables()
    c = _conn()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = c.execute('UPDATE purchase_orders SET status=?, decided_by=?, decided_at=? '
                    'WHERE id=?', (status, session['user_id'], now, oid))
    c.commit()
    row = c.execute('SELECT created_by FROM purchase_orders WHERE id=?',
                    (oid,)).fetchone() if cur.rowcount else None
    c.close()
    if not row:
        return jsonify({'status': 'error', 'message': 'Заявка не найдена'}), 404
    if row['created_by'] and row['created_by'] != session['user_id']:
        try:
            from company_rules import _vk_ids_by_user, _send_vk_user
            umap = _vk_ids_by_user()
            for vk_id in umap.get(row['created_by'], []):
                try:
                    _send_vk_user(vk_id, f"Заявка #{oid} {labels[status]}")
                except Exception:
                    pass
        except Exception:
            pass
    return jsonify({'status': 'success', 'message': f'Заявка #{oid} {labels[status]}'})


