# -*- coding: utf-8 -*-
"""
sales_analytics.py — полноценный анализ продаж, приёмок и ЗП.

Источники (schedule.db):
  * 1С:  sync_sales / sync_sale_items, sync_receipts / sync_receipt_items,
         sync_nomenclature, sync_barcodes, sync_counterparties
  * Программа: users, work_sessions (открытые кассы по дням),
         work_schedule (график), products_1c (розничные цены + штрихкоды)

Возможности:
  1. Сверка «касса по сменам» vs «продажи из 1С» по сотруднику и дням.
  2. ЗП по порогам выручки за смену (analytics_config.json).
  3. Продуктовый профиль продавца по дням.
  4. Аномалии: цена ниже розницы, завышенные скидки, всплески количества.
  5. Приёмки (закупки) против продаж: остатки, перезакуп, продажи без приёмки.
  6. Сезонность и динамика по месяцам / группам товаров.
  7. Конкретные рекомендации и HTML-отчёт.
"""
import os
import io
import json
import sqlite3
import re
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    """Нормализация названия для сравнения."""
    if not s:
        return ''
    return re.sub(r'\s+', ' ', str(s).strip().lower())


def _money(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def fmt_money(x):
    return '{:,.2f}'.format(_money(x)).replace(',', ' ')


def day_pay(revenue, cfg):
    """Оплата смены по порогам выручки."""
    revenue = _money(revenue)
    salary_cfg = cfg.get('salary', {})
    tiers = salary_cfg.get('tiers', []) or []
    floor = _money(salary_cfg.get('floor', 1600))
    best = floor
    for t in tiers:
        if revenue >= _money(t.get('min_revenue')):
            best = _money(t.get('pay'))
    return max(floor, best)


def load_config():
    path = os.path.join(BASE_DIR, 'analytics_config.json')
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


class SalesAnalytics:
    def __init__(self, db_path, cfg=None):
        self.cfg = cfg or load_config()
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.users = []
        self.sessions = []
        self.sales = []
        self.items = []
        self.receipts = []
        self.rec_items = []
        self.nomenclature = {}
        self.price_map = {}
        self.barcodes_by_guid = {}
        self._load()

    # ---------- загрузка ----------
    def _load(self):
        c = self.conn
        self.users = [dict(r) for r in c.execute(
            'SELECT id, username, full_name, role FROM users ORDER BY id')]

        self.sessions = [dict(r) for r in c.execute(
            'SELECT id, user_id, year, month, day, revenue_total, '
            'acquiring_amount, evening_cash, status FROM work_sessions')]

        self.sales = [dict(r) for r in c.execute(
            'SELECT guid, date, number, seller_name, warehouse_name, '
            'cash_register, total_sum, organization_name FROM sync_sales')]

        self.items = [dict(r) for r in c.execute(
            'SELECT sale_guid, nomenclature_guid, nomenclature_code, '
            'nomenclature_name, quantity, price, sum FROM sync_sale_items')]

        self.receipts = [dict(r) for r in c.execute(
            'SELECT guid, date, number, operation_type, organization_name, '
            'total_sum FROM sync_receipts')]

        self.rec_items = [dict(r) for r in c.execute(
            'SELECT receipt_guid, nomenclature_code, nomenclature_name, '
            'quantity, price, sum FROM sync_receipt_items')]

        for r in c.execute('SELECT guid, code, name, group_name FROM sync_nomenclature'):
            self.nomenclature[r['guid']] = {
                'code': r['code'], 'name': r['name'], 'group': r['group_name']}

        for r in c.execute('SELECT name, retail_price, purchase_price, barcode_main, '
                           'group_name, category FROM products_1c'):
            k = norm(r['name'])
            if k and k not in self.price_map:
                self.price_map[k] = {
                    'retail': _money(r['retail_price']),
                    'purchase': _money(r['purchase_price']),
                    'barcode': r['barcode_main'],
                    'group': r['group_name'] or r['category'],
                }

        for r in c.execute('SELECT barcode, nomenclature_guid FROM sync_barcodes'):
            self.barcodes_by_guid.setdefault(r['nomenclature_guid'], set()).add(r['barcode'])

    # ---------- сопоставление продавца 1С с сотрудником ----------
    def resolve_seller(self, seller_name):
        """Возвращает (user_id, display_name)."""
        sn = norm(seller_name)
        if not sn:
            return (None, 'Продавец не указан')
        alias_cfg = self.cfg.get('sellers_map', {})
        if sn in alias_cfg:
            target = norm(alias_cfg[sn])
            for u in self.users:
                if norm(u.get('username', '')) == target:
                    return (u['id'], u.get('full_name') or u.get('username'))
        best = None
        for u in self.users:
            un = norm(u.get('username') or '')
            hay = norm((u.get('full_name') or '') + ' ' + un)
            if un and un in sn:
                best = u
                break
            if hay and hay in sn:
                best = u
                break
            if hay:
                hit = False
                for tok in sn.replace('-', ' ').split():
                    if len(tok) > 2 and tok in hay:
                        hit = True
                        break
                if hit:
                    best = u
                    break
        if best:
            return (best['id'], best.get('full_name') or best.get('username'))
        return (None, seller_name)

    @staticmethod
    def _day(ts):
        s = (ts or '')[:10]
        return s if re.match(r'\d{4}-\d{2}-\d{2}', s) else None

    def session_date(self, sess):
        try:
            y = int(sess.get('year')); m = int(sess.get('month')); d = int(sess.get('day'))
            return '%04d-%02d-%02d' % (y, m, d)
        except (TypeError, ValueError):
            return None

    # ---------- вспомогательное ----------
    @staticmethod
    def _product_ident(item):
        name = (item.get('nomenclature_name') or '').strip()
        if name:
            return norm(name), name
        code = (item.get('nomenclature_code') or '').strip()
        return norm(code) or '?', code or '?'

    def _item_meta(self, item):
        """Доп. данные товара: группа, штрихкод, розница."""
        guid = item.get('nomenclature_guid')
        code = item.get('nomenclature_code') or ''
        name = (item.get('nomenclature_name') or '').strip()
        nkey = norm(name)
        retail = 0.0
        if nkey in self.price_map:
            retail = self.price_map[nkey].get('retail', 0.0) or 0.0
        barcode = None
        if nkey in self.price_map and self.price_map[nkey].get('barcode'):
            barcode = self.price_map[nkey]['barcode']
        elif guid and self.barcodes_by_guid.get(guid):
            barcode = sorted(self.barcodes_by_guid[guid])[0]
        group = None
        if nkey in self.price_map:
            group = self.price_map[nkey].get('group')
        if not group and guid in self.nomenclature:
            group = self.nomenclature[guid].get('group')
        return {'retail': retail, 'barcode': barcode, 'group': group,
                'code': code, 'display': name or code}

    # ---------- основной анализ ----------
    def analyze(self):
        rep = {'cfg': self.cfg,
               'meta': {'generated': datetime.now().strftime('%d.%m.%Y %H:%M')}}
        cfg_a = self.cfg.get('anomaly', {})
        tol_rub = float(cfg_a.get('cash_delta_tolerance_rub', 500))
        tol_ratio = float(cfg_a.get('cash_delta_tolerance_ratio', 1.05))

        # Продажи 1С, привязанные к сотрудникам
        # Кто открыл кассу в день (по сменам) — для корректной привязки продаж
        sess_day_users = {}
        for sess in self.sessions:
            d = self.session_date(sess)
            if d:
                sess_day_users.setdefault(d, set()).add(sess.get('user_id'))
        uname_of = {u['id']: (u.get('full_name') or u.get('username'))
                    for u in self.users}

        sales_rows = []
        by_day_1c = defaultdict(float)
        by_day_docs = defaultdict(int)
        by_month_1c = defaultdict(lambda: {'sum': 0.0, 'docs': 0})

        for s in self.sales:
            day = self._day(s.get('date'))
            if not day:
                continue
            uid, disp = self.resolve_seller(s.get('seller_name'))
            # Если продавца по имени нет/не совпадает со сменой этого дня,
            # а смену в этот день открыл ровно один сотрудник — относим
            # продажи дня к нему (кассу закрывал реальный работник).
            if day in sess_day_users:
                users_today = sess_day_users[day]
                if len(users_today) == 1 and uid not in users_today:
                    uid = next(iter(users_today))
                    disp = uname_of.get(uid, disp)
            total = _money(s.get('total_sum'))
            sales_rows.append({'day': day, 'ym': day[:7], 'uid': uid,
                               'seller': disp, 'sum': total,
                               'number': s.get('number'),
                               'warehouse': s.get('warehouse_name'),
                               'cash': s.get('cash_register'),
                               'guid': s.get('guid')})
            if uid:
                by_day_1c[(uid, day)] += total
                by_day_docs[(uid, day)] += 1
            by_month_1c[day[:7]]['sum'] += total
            by_month_1c[day[:7]]['docs'] += 1

        items_by_sale = defaultdict(list)
        for it in self.items:
            items_by_sale[it['sale_guid']].append(it)
        sale_items = []
        for sr in sales_rows:
            for it in items_by_sale.get(sr['guid'], []):
                sale_items.append({'day': sr['day'], 'ym': sr['day'][:7],
                                   'uid': sr['uid'], 'seller': sr['seller'],
                                   'item': dict(it)})

        # Смены программы (касса)
        sess_by_day = defaultdict(lambda: {'rev': 0.0, 'cashless': 0.0})
        for sess in self.sessions:
            day = self.session_date(sess)
            if not day:
                continue
            rev = _money(sess.get('revenue_total'))
            acq = _money(sess.get('acquiring_amount'))
            k = (sess.get('user_id'), day)
            sess_by_day[k]['rev'] += rev
            sess_by_day[k]['cashless'] += acq

        # Сверка по дням: касса vs 1С
        cash_rows = []
        all_keys = set(sess_by_day) | set(by_day_1c)
        for (uid, day) in sorted(all_keys):
            cash = sess_by_day.get((uid, day), {}).get('rev', 0.0)
            rev1c = by_day_1c.get((uid, day), 0.0)
            if not uid:
                continue
            if cash == 0 and rev1c == 0:
                continue
            delta = cash - rev1c
            flag = 'ok'
            if cash == 0 and rev1c > 0:
                flag = 'no_session'
            elif rev1c == 0 and cash > 0:
                flag = 'no_1c'
            elif abs(delta) > tol_rub and (rev1c == 0 or abs(delta) / rev1c > tol_ratio):
                flag = 'delta'
            cash_rows.append({'uid': uid, 'day': day, 'cash': cash, 'rev1c': rev1c,
                              'delta': delta, 'flag': flag,
                              'docs': by_day_docs.get((uid, day), 0)})

        # ЗП по продавцам
        emp_salary = defaultdict(lambda: {'days': 0, 'cash_days': 0,
                                          'rev_1c': 0.0, 'rev_cash': 0.0,
                                          'salary': 0.0,
                                          'monthly': defaultdict(
                                              lambda: {'days': 0, 'rev': 0.0,
                                                       'pay': 0.0})})
        for row in cash_rows:
            d = emp_salary[row['uid']]
            d['days'] += 1
            if row['cash'] > 0:
                d['cash_days'] += 1
                d['rev_cash'] += row['cash']
            d['rev_1c'] += row['rev1c']
            base = row['rev1c'] if row['rev1c'] > 0 else row['cash']
            pay = day_pay(base, self.cfg)
            d['salary'] += pay
            m = d['monthly'][row['day'][:7]]
            m['days'] += 1
            m['rev'] += base
            m['pay'] += pay

        employee_summary = []
        for u in self.users:
            d = emp_salary.get(u['id'])
            if not d or d['days'] == 0:
                continue
            monthly = [{'ym': ym, **mm} for ym, mm in sorted(d['monthly'].items())]
            employee_summary.append({
                'user_id': u['id'], 'name': u.get('full_name') or u.get('username'),
                'username': u.get('username'), 'role': u.get('role'),
                'days': d['days'], 'cash_days': d['cash_days'],
                'rev_1c': d['rev_1c'], 'rev_cash': d['rev_cash'],
                'salary': d['salary'], 'monthly': monthly})

        # ---- Продуктовые профили продавцов и всплески ----
        # ключ товара: нормализованное имя (fallback код)
        prod_agg = defaultdict(lambda: {'qty': 0.0, 'sum': 0.0})     # (uid,key)
        spike = defaultdict(float)                                    # (uid,key,day)
        day_any_sold = defaultdict(set)                               # uid -> days
        disp_of = {}
        meta_of = {}

        for si in sale_items:
            if not si['uid']:
                continue
            it = si['item']
            key, disp = self._product_ident(it)
            meta = self._item_meta(it)
            q = _money(it.get('quantity'))
            sm = _money(it.get('sum'))
            kk = (si['uid'], key)
            prod_agg[kk]['qty'] += q
            prod_agg[kk]['sum'] += sm
            disp_of[kk] = disp
            meta_of[kk] = meta
            day_any_sold[si['uid']].add(si['day'])
            spike[(si['uid'], key, si['day'])] += q

        # аномалии: всплески количества (по продавцу), заниженная цена, скидка
        cfg_a = self.cfg.get('anomaly', {})
        min_qty = int(cfg_a.get('qty_spike_min', 5))
        fact = float(cfg_a.get('qty_spike_factor', 3.0))
        max_disc = float(cfg_a.get('max_discount_ok', 0.30))
        drop_ok = float(cfg_a.get('price_drop_ok', 0.85))

        qty_anomalies = []
        # для каждого (продавец, товар) среднее количество в день продажи
        per_seller_prod = defaultdict(list)  # (uid,key) -> [qty per sold day]
        for (uid, key, day), q in spike.items():
            per_seller_prod[(uid, key)].append(q)
        for (uid, key), qts in per_seller_prod.items():
            qts = sorted(qts, reverse=True)
            mean = sum(qts) / len(qts)
            for day_q in qts:
                if day_q >= min_qty and mean > 0 and day_q >= fact * max(mean, 2.0) \
                        and day_q >= fact * (mean if len(qts) > 1 else 1):
                    pass
            # простая эвристика: максимальный день заметно выше среднего остальных дней
            if len(qts) >= 3 and qts[0] >= min_qty:
                rest = qts[1:]
                rest_mean = sum(rest) / len(rest) if rest else 0
                if rest_mean > 0 and qts[0] >= fact * rest_mean:
                    kk = (uid, key)
                    qty_anomalies.append({'seller_id': uid,
                                          'seller': disp_of.get(kk, ''),
                                          'product': disp_of.get(kk, key),
                                          'code': meta_of.get(kk, {}).get('code'),
                                          'barcode': meta_of.get(kk, {}).get('barcode'),
                                          'top_day_qty': round(qts[0], 2),
                                          'usual_qty': round(rest_mean, 2),
                                          'days': len(qts)})

        # заниженная цена/скидка относительно розницы прайса
        price_anomalies = []
        price_seller = defaultdict(lambda: {'qty': 0.0, 'sum': 0.0})  # (uid,key)
        for si in sale_items:
            if not si['uid']:
                continue
            it = si['item']
            key, _ = self._product_ident(it)
            kk = (si['uid'], key)
            price_seller[kk]['qty'] += _money(it.get('quantity'))
            price_seller[kk]['sum'] += _money(it.get('sum'))
        for (uid, key), ag in price_seller.items():
            meta = meta_of.get((uid, key), {})
            retail = _money(meta.get('retail'))
            if not retail or ag['qty'] <= 0:
                continue
            avg = ag['sum'] / ag['qty']
            ratio = avg / retail
            if ratio <= drop_ok:
                money_loss = (retail - avg) * ag['qty']
                disc = 1 - ratio
                price_anomalies.append({
                    'seller_id': uid,
                    'seller': disp_of.get((uid, key), ''),
                    'product': disp_of.get((uid, key), key),
                    'barcode': meta.get('barcode'),
                    'qty': round(ag['qty'], 2),
                    'sold_avg_price': round(avg, 2),
                    'retail_price': retail,
                    'discount': round(disc * 100, 1),
                    'money_loss': round(money_loss, 2)})

        # ---- Профили продавцов (топ товаров) ----
        profiles = []
        for u in self.users:
            uitems = [(k, ag) for k, ag in prod_agg.items() if k[0] == u['id']]
            if not uitems:
                continue
            uitems.sort(key=lambda x: -x[1]['sum'])
            top = []
            for k, ag in uitems[:15]:
                meta = meta_of.get(k, {})
                top.append({'product': disp_of.get(k, k[1]),
                            'code': meta.get('code'), 'barcode': meta.get('barcode'),
                            'qty': round(ag['qty'], 2),
                            'sum': round(ag['sum'], 2),
                            'days_sold': len(per_seller_prod.get(k, []))})
            profiles.append({'user_id': u['id'],
                             'name': u.get('full_name') or u.get('username'),
                             'days_worked': len(day_any_sold.get(u['id'], set())),
                             'products': len(uitems), 'top': top})

        # ---- Итоги по товарам (все продавцы) для сверки с приёмками ----
        prod_total = defaultdict(lambda: {'qty': 0.0, 'sum': 0.0})
        for si in sale_items:
            key, _ = self._product_ident(si['item'])
            prod_total[key]['qty'] += _money(si['item'].get('quantity'))
            prod_total[key]['sum'] += _money(si['item'].get('sum'))

        # ---- Приёмки (закупки) против продаж ----
        recv_total = defaultdict(lambda: {'qty': 0.0, 'sum': 0.0, 'months': set()})
        recv_by_ym = defaultdict(lambda: {'qty': 0.0, 'sum': 0.0})
        recv_month_items = defaultdict(lambda: defaultdict(lambda: {'qty': 0.0}))
        for ri in self.rec_items:
            key, disp = self._product_ident(ri)
            # найти месяц приёмки по документу
            ym = None
            for rc in self.receipts:
                if rc.get('guid') == ri['receipt_guid']:
                    day = self._day(rc.get('date'))
                    if day:
                        ym = day[:7]
                    break
            if ym:
                recv_by_ym[ym]['qty'] += _money(ri.get('quantity'))
                recv_by_ym[ym]['sum'] += _money(ri.get('sum'))
                recv_month_items[ym][key]['qty'] += _money(ri.get('quantity'))
            recv_total[key]['qty'] += _money(ri.get('quantity'))
            recv_total[key]['sum'] += _money(ri.get('sum'))
            recv_total[key]['months'].add(ym or '?')

        overstock = []        # закуплено много / не продаётся
        no_receipt = []       # продано, но не оприходовано
        recv_meta = {}
        for ri in self.rec_items:
            key, disp = self._product_ident(ri)
            if key not in recv_meta:
                recv_meta[key] = {'display': disp, **self._item_meta(ri)}
        for key in set(recv_total) | set(prod_total):
            rq = recv_total[key]['qty']
            sq = prod_total[key]['qty']
            disp = recv_meta.get(key, {}).get('display') or key
            if rq > 0 and sq == 0 and rq >= 5:
                overstock.append({'product': disp, 'received': round(rq, 2),
                                  'sold': 0,
                                  'barcode': recv_meta.get(key, {}).get('barcode')})
            elif rq > 0 and sq > 0 and rq >= 5 and rq >= 3 * sq:
                overstock.append({'product': disp, 'received': round(rq, 2),
                                  'sold': round(sq, 2),
                                  'barcode': recv_meta.get(key, {}).get('barcode')})
            elif sq > 0 and rq == 0:
                meta = recv_meta.get(key) or {'display': disp}
                no_receipt.append({'product': disp,
                                   'sold': round(sq, 2),
                                   'barcode': meta.get('barcode')})
        overstock.sort(key=lambda x: -x['received'])
        no_receipt.sort(key=lambda x: -x['sold'])

        # ---- Сезонность: помесячно ----
        sale_qty_ym = defaultdict(float)
        for si in sale_items:
            sale_qty_ym[si['ym']] += _money(si['item'].get('quantity'))
        yms = sorted(set(list(by_month_1c.keys()) + list(sale_qty_ym.keys()) +
                         list(recv_by_ym.keys())))
        season = []
        for ym in yms:
            season.append({'ym': ym,
                           'sales_docs': by_month_1c[ym]['docs'],
                           'sales_sum': round(by_month_1c[ym]['sum'], 2),
                           'sales_qty': round(sale_qty_ym[ym], 2),
                           'recv_qty': round(recv_by_ym[ym]['qty'], 2),
                           'recv_sum': round(recv_by_ym[ym]['sum'], 2)})

        # ---- Топ товаров по группам за последние месяцы ----
        group_ym = defaultdict(lambda: defaultdict(float))
        for si in sale_items:
            meta = self._item_meta(si['item'])
            g = meta.get('group') or 'Без группы'
            group_ym[g][si['ym']] += _money(si['item'].get('quantity'))
        season_groups = []
        for g, bym in group_ym.items():
            months = sorted(bym)
            last = months[-1]
            prev = months[-2] if len(months) > 1 else None
            season_groups.append({
                'group': g, 'last_month': last,
                'last_qty': round(bym[last], 2),
                'prev_qty': round(bym[prev], 2) if prev else None,
                'prev_month': prev,
                'change_pct': round((bym[last] - bym[prev]) / bym[prev] * 100, 1)
                if prev and bym[prev] else None})
        season_groups.sort(key=lambda x: -(x['last_qty'] or 0))

        # ---- Рекомендации ----
        recs = []
        cash_bad = [r for r in cash_rows if r['flag'] != 'ok']
        if cash_bad:
            recs.append('Сверка касса/1С: найдено %d дней с расхождениями — '
                        'смотрите раздел «Сверка по дням».' % len(cash_bad))
        for u in employee_summary:
            if u['rev_cash'] > 0 and u['rev_1c'] > 0 and u['rev_cash'] != u['rev_1c']:
                diff = u['rev_cash'] - u['rev_1c']
                pct = diff / u['rev_1c'] * 100 if u['rev_1c'] else 0
                recs.append('%s: за период выручка по кассе отличается от 1С на %s ₽ '
                            '(%+.1f%%) — проверьте закрытие смен и отчёты о продажах.'
                            % (u['name'], fmt_money(abs(diff)), pct))
        if price_anomalies:
            loss = sum(a['money_loss'] for a in price_anomalies)
            recs.append('По %d позициям товар продавался ниже розничной цены, '
                        'суммарная недополученная выручка ≈ %s ₽ — '
                        'проверьте акции/скидки и цены в 1С.'
                        % (len(price_anomalies), fmt_money(loss)))
        if qty_anomalies:
            recs.append('Найдено %d всплесков количества продаж у продавцов — '
                        'смотрите раздел «Аномалии».' % len(qty_anomalies))
        if no_receipt:
            recs.append('%d товаров проданы, но не оприходованы (приёмки нет).'
                        % len(no_receipt))
        if overstock:
            recs.append('%d позиций закуплено заметно больше, чем продано — '
                        'не заказывайте их до распродажи остатков.'
                        % len(overstock))
        grow = [g for g in season_groups if g['change_pct'] and g['change_pct'] > 30]
        fall = [g for g in season_groups if g['change_pct'] and g['change_pct'] < -30]
        if grow:
            recs.append('Растущие группы товаров (к закупке): %s.'
                        % ', '.join('%s (+%s%%)' % (g['group'], g['change_pct'])
                                    for g in grow[:3]))
        if fall:
            recs.append('Падающие группы (не закупать впрок): %s.'
                        % ', '.join('%s (%s%%)' % (g['group'], g['change_pct'])
                                    for g in fall[:3]))
        if not recs:
            recs.append('Явных проблем не обнаружено. Продолжайте ежедневную сверку.')
        for u in employee_summary:
            if u['monthly']:
                lm = u['monthly'][-1]
                recs.append('%s: за %s отработано %d смен, выручка %s ₽, '
                            'оплата по порогам = %s ₽.'
                            % (u['name'], lm['ym'], lm['days'],
                               fmt_money(lm['rev']), fmt_money(lm['pay'])))

        # ---- Сборка отчёта ----
        sales_days = [r['day'] for r in sales_rows]
        cash_days = [r['day'] for r in cash_rows if r['cash'] > 0]
        rec_days = [d for d in (self._day(r.get('date')) for r in self.receipts) if d]
        rep['periods'] = {
            'sales': (min(sales_days) if sales_days else '-',
                      max(sales_days) if sales_days else '-'),
            'sessions': (min(cash_days) if cash_days else '-',
                         max(cash_days) if cash_days else '-'),
            'receipts': (min(rec_days) if rec_days else '-',
                         max(rec_days) if rec_days else '-')}
        rep['summary'] = {
            'sales_docs': len(sales_rows),
            'sale_items': len(sale_items),
            'revenue_1c': round(sum(r['sum'] for r in sales_rows), 2),
            'cash_sessions': len(cash_days),
            'revenue_cash': round(sum(r['cash'] for r in cash_rows), 2),
            'receipt_docs': len(self.receipts),
            'receipt_items': len(self.rec_items),
            'receipt_sum': round(sum(_money(r['sum']) for r in self.rec_items), 2),
            'overlap_days': len([r for r in cash_rows
                                 if r['cash'] > 0 and r['rev1c'] > 0])}
        rep['cash_rows'] = cash_rows
        rep['employees'] = employee_summary
        rep['profiles'] = profiles
        rep['price_anomalies'] = sorted(price_anomalies,
                                        key=lambda x: -x['money_loss'])[:80]
        rep['qty_anomalies'] = sorted(qty_anomalies,
                                      key=lambda x: -x['top_day_qty'])[:80]
        rep['overstock'] = overstock[:120]
        rep['no_receipt'] = no_receipt[:120]
        rep['season'] = season
        rep['season_groups'] = season_groups[:40]
        rep['recommendations'] = recs
        return rep


