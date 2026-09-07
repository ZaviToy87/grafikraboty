# -*- coding: utf-8 -*-
"""Генератор HTML-отчёта «Анализ продаж и ЗП» + CLI."""
import os
import io
import json
import webbrowser
from datetime import datetime

import sales_analytics as sa

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def esc(v):
    return str(v if v is not None else '').replace('&', '&amp;').replace(
        '<', '&lt;').replace('>', '&gt;')


CSS = """
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f5fb;color:#222}
.wrap{max-width:1280px;margin:0 auto;padding:18px}
h1{font-size:22px;margin:0 0 4px}
h2{font-size:17px;margin:28px 0 10px;padding:8px 12px;background:#6366f1;color:#fff;border-radius:8px}
.meta{color:#666;font-size:13px;margin-bottom:12px}
.cards{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.card{background:#fff;border-radius:10px;padding:12px 16px;box-shadow:0 1px 4px rgba(0,0,0,.08);min-width:150px}
.card .n{font-size:20px;font-weight:700;color:#1f2937}
.card .l{font-size:12px;color:#6b7280}
table{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden;font-size:13px}
th{background:#eef0ff;padding:8px;text-align:left;white-space:nowrap}
td{padding:7px 8px;border-top:1px solid #eef0f4;vertical-align:top}
tr:hover td{background:#fafaff}
.b{font-weight:600}
.r{color:#dc2626}.g{color:#16a34a}.o{color:#d97706}
.rec{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 14px;margin:6px 0;font-size:14px}
.flag-ok{color:#16a34a}.flag-delta{color:#dc2626;font-weight:700}
.flag-no_1c{color:#d97706}.flag-no_session{color:#dc2626}
.note{color:#9ca3af;font-size:12px}
@media print{body{background:#fff}.wrap{max-width:100%}}
"""


def table(headers, rows):
    h = ''.join('<th>%s</th>' % esc(x) for x in headers)
    body = []
    for r in rows:
        body.append('<tr>' + ''.join('<td>%s</td>' % c for c in r) + '</tr>')
    return ('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
            % (h, ''.join(body) if body else '<tr><td>Нет данных</td></tr>'))


def flag_text(f):
    return {'ok': 'ок', 'delta': 'расхождение', 'no_1c': 'нет в 1С',
            'no_session': 'нет смены'}.get(f, f)


def build_html(rep):
    out = []
    meta = rep.get('meta', {})
    cfg = rep.get('cfg', {})
    s = rep.get('summary', {})
    per = rep.get('periods', {})
    out.append('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">')
    out.append('<title>Анализ продаж и ЗП</title><style>%s</style></head><body>'
               % CSS)
    out.append('<div class="wrap">')
    out.append('<h1>📊 Анализ продаж, приёмок и зарплат</h1>')
    out.append('<div class="meta">Сформировано: %s &nbsp;|&nbsp; '
               'Продажи 1С: %s … %s &nbsp;|&nbsp; Касса (смены): %s … %s'
               % (esc(meta.get('generated', '')), esc(per['sales'][0]),
                  esc(per['sales'][1]), esc(per['sessions'][0]),
                  esc(per['sessions'][1])))
    out.append('Приёмки (закупки): %s … %s</div>'
               % (esc(per['receipts'][0]), esc(per['receipts'][1])))
    if s.get('overlap_days', 0) == 0:
        out.append('<div class="rec" style="border-color:#fca5a5;background:#fef2f2">'
                   '⚠️ Периоды смен (касса) и продаж из 1С <b>не пересекаются</b> — '
                   'сверка день-в-день и расчёт ЗП будут точными после загрузки '
                   'свежей выгрузки 1С за те же даты, что и смены.</div>')

    out.append('<div class="cards">')
    cards = [('Продаж из 1С', s['sales_docs'], ''),
             ('Выручка 1С', s['revenue_1c'], ''),
             ('Продано позиций', s['sale_items'], ''),
             ('Смен (касса)', s['cash_sessions'], ''),
             ('Выручка по кассе', s['revenue_cash'], ''),
             ('Приёмок', s['receipt_docs'], ''),
             ('Сумма приёмок', s['receipt_sum'], '')]
    for label, val, note in cards:
        out.append('<div class="card"><div class="n">%s</div>'
                   '<div class="l">%s</div></div>'
                   % (esc(val if isinstance(val, str) else sa.fmt_money(val)),
                      esc(label)))
    out.append('</div>')

    # Рекомендации
    out.append('<h2>✅ Рекомендации</h2>')
    for r in rep.get('recommendations', []):
        out.append('<div class="rec">%s</div>' % esc(r))

    # ЗП по сотрудникам
    out.append('<h2>💰 Зарплата по порогам выручки за смену</h2>')
    emp_rows = []
    for e in rep.get('employees', []):
        monthly = e.get('monthly', [])
        ms = '; '.join('%s: %d см., выручка %s ₽, оплата %s ₽'
                       % (m['ym'], m['days'], sa.fmt_money(m['rev']),
                          sa.fmt_money(m['pay'])) for m in monthly)
        emp_rows.append([esc(e['name']), e['days'], e['cash_days'],
                         sa.fmt_money(e['rev_1c']), sa.fmt_money(e['rev_cash']),
                         sa.fmt_money(e['salary']), esc(ms)])
    out.append(table(['Сотрудник', 'Дней сверки', 'Смен (касса)',
                      'Выручка 1С', 'Выручка касса', 'Оплата (расчёт)',
                      'Детализация по месяцам'], emp_rows))

    # Сверка по дням (только проблемные и сводка)
    cash_rows = rep.get('cash_rows', [])
    bad = [r for r in cash_rows if r['flag'] != 'ok']
    out.append('<h2>🔍 Сверка «касса смены ↔ продажи 1С»</h2>')
    out.append('<div class="note">Проблемных дней: %d из %d</div>'
               % (len(bad), len(cash_rows)))
    names = {e['user_id']: e['name'] for e in rep.get('employees', [])}
    rows = []
    shown = bad if bad else cash_rows[:30]
    for r in shown:
        cls = 'flag-%s' % r['flag']
        rows.append([esc(r['day']), esc(names.get(r['uid'], r['uid'])),
                     sa.fmt_money(r['cash']), sa.fmt_money(r['rev1c']),
                     sa.fmt_money(r['delta']), r['docs'],
                     '<span class="%s">%s</span>' % (cls, esc(flag_text(r['flag'])))])
    out.append(table(['Дата', 'Сотрудник', 'Касса ₽', '1С ₽', 'Δ ₽',
                      'Док.', 'Статус'], rows))

    # Профили продавцов
    out.append('<h2>🛒 Продуктовые профили продавцов</h2>')
    for p in rep.get('profiles', []):
        out.append('<h3>%s <span class="note">(%d уникальных товаров, '
                   '%d дней продаж)</span></h3>'
                   % (esc(p['name']), p['products'], p['days_worked']))
        rows = []
        for t in p.get('top', []):
            rows.append([esc(t['product']), esc(t['code'] or ''),
                         esc(t['barcode'] or ''), t['qty'],
                         sa.fmt_money(t['sum']), t['days_sold']])
        out.append(table(['Товар', 'Код', 'Штрихкод', 'Кол-во', 'Сумма ₽',
                          'Дней продаж'], rows))

    # Аномалии
    out.append('<h2>⚠️ Аномалии: цена ниже розницы / скидки</h2>')
    rows = []
    for a in rep.get('price_anomalies', []):
        rows.append([esc(a['seller']), esc(a['product']), esc(a['barcode'] or ''),
                     a['qty'], sa.fmt_money(a['sold_avg_price']),
                     sa.fmt_money(a['retail_price']), a['discount'],
                     '<span class="r">%s</span>' % sa.fmt_money(a['money_loss'])])
    out.append(table(['Продавец', 'Товар', 'Штрихкод', 'Кол-во', 'Ср. цена ₽',
                      'Розница ₽', 'Скидка %', 'Потеря ₽'], rows))

    out.append('<h2>📈 Всплески количества продаж у продавцов</h2>')
    rows = []
    for a in rep.get('qty_anomalies', []):
        rows.append([esc(a['seller']), esc(a['product']), esc(a['barcode'] or ''),
                     a['top_day_qty'], a['usual_qty'], a['days']])
    out.append(table(['Продавец', 'Товар', 'Штрихкод', 'Макс. за день',
                      'Обычно за день', 'Дней продаж'], rows))

    # Приёмки vs продажи
    out.append('<h2>📦 Закупки (приёмки) против продаж</h2>')
    out.append('<h3>Перезакуп / не продаётся</h3>')
    rows = []
    for a in rep.get('overstock', []):
        rows.append([esc(a['product']), esc(a['barcode'] or ''),
                     a['received'], a['sold']])
    out.append(table(['Товар', 'Штрихкод', 'Принято', 'Продано'], rows))
    out.append('<h3>Продано без приёмки (не оприходовано)</h3>')
    rows = []
    for a in rep.get('no_receipt', []):
        rows.append([esc(a['product']), esc(a['barcode'] or ''), a['sold']])
    out.append(table(['Товар', 'Штрихкод', 'Продано'], rows))

    # Сезонность
    out.append('<h2>🗓️ Сезонность</h2>')
    rows = []
    for m in rep.get('season', []):
        rows.append([m['ym'], m['sales_docs'], sa.fmt_money(m['sales_sum']),
                     m['sales_qty'], m['recv_qty'], sa.fmt_money(m['recv_sum'])])
    out.append(table(['Месяц', 'Продаж', 'Сумма ₽', 'Продано шт',
                      'Принято шт', 'Сумма приёмок ₽'], rows))
    out.append('<h3>Группы товаров: динамика последних месяцев</h3>')
    rows = []
    for g in rep.get('season_groups', []):
        ch = ('%s%%' % g['change_pct'] if g['change_pct'] is not None else '-')
        ch_cls = 'g' if (g['change_pct'] or 0) >= 0 else 'r'
        rows.append([esc(g['group']), g['last_month'], g['last_qty'],
                     g['prev_month'], g['prev_qty'] if g['prev_qty'] is not None else '-',
                     '<span class="%s">%s</span>' % (ch_cls, ch)])
    out.append(table(['Группа', 'Последний мес.', 'Продано шт', 'Пред. мес.',
                      'Пред. шт', 'Изменение'], rows))

    out.append('<div class="note" style="margin-top:18px">Отчёт сформирован '
               'модулем sales_analytics.py. Настройки порогов ЗП и '
               'соответствий продавцов — analytics_config.json.</div>')
    out.append('</div></body></html>')
    return '\n'.join(out)


def main(argv=None):
    argv = argv if argv is not None else []
    db = os.path.join(BASE_DIR, 'schedule.db')
    report_dir = os.path.join(BASE_DIR, 'sales_reports')
    for a in argv:
        if a in ('-h', '--help'):
            print('Запуск: python sales_report.py [путь_к_schedule.db]')
            return 0
        if a.endswith('.db'):
            db = a
    cfg = sa.load_config()
    if os.path.isdir(cfg.get('paths', {}).get('report_dir', report_dir)):
        report_dir = cfg['paths']['report_dir']
    print('Анализ базы:', db)
    engine = sa.SalesAnalytics(db, cfg)
    rep = engine.analyze()
    os.makedirs(report_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = os.path.join(report_dir, 'sales_report_%s.html' % stamp)
    json_path = os.path.join(report_dir, 'sales_report_%s.json' % stamp)
    with io.open(html_path, 'w', encoding='utf-8') as f:
        f.write(build_html(rep))
    with io.open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, default=str)
    print('Отчёт сохранён:')
    print(' ', html_path)
    print(' ', json_path)
    print()
    print('ИТОГО: продаж=%d, выручка 1С=%s, смен=%d, выручка касса=%s, '
          'приёмок=%d (сумма %s)'
          % (rep['summary']['sales_docs'],
             sa.fmt_money(rep['summary']['revenue_1c']),
             rep['summary']['cash_sessions'],
             sa.fmt_money(rep['summary']['revenue_cash']),
             rep['summary']['receipt_docs'],
             sa.fmt_money(rep['summary']['receipt_sum'])))
    for e in rep['employees']:
        print('Сотрудник %s: дней=%d, выручка_1с=%s, касса=%s, '
              'оплата_по_порогам=%s'
              % (e['name'], e['days'], sa.fmt_money(e['rev_1c']),
                 sa.fmt_money(e['rev_cash']), sa.fmt_money(e['salary'])))
    print('Проблемных дней сверки:', len([r for r in rep['cash_rows']
                                          if r['flag'] != 'ok']))
    print('Аномалий цены:', len(rep['price_anomalies']),
          '| Всплесков:', len(rep['qty_anomalies']),
          '| Перезакуп:', len(rep['overstock']),
          '| Продано без приёмки:', len(rep['no_receipt']))
    webbrowser.open('file:///' + html_path.replace('\\', '/'))
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
