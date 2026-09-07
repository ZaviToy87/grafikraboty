# -*- coding: utf-8 -*-
"""
fix_margins.py — восстановление приходной (закупочной) цены по наценке.

Наценка = (розница − закупка) / закупка × 100%.
Приходная цена = розница / (1 + наценка/100).

Правила наценки (правьте прямо здесь):
  корма:        сухие/эконом ≈ 30%, влажные ≈ 45%, премиум-бренды ≈ 60%
                (в целом корма 25–60%)
  лакомства:    ≈ 45%
  аксессуары/препараты/наполнители: ≈ 85%
  прочее:       ≈ 40% (можно поменять DEFAULT_MARGIN)

Запуск:
  python fix_margins.py          # показать, сколько и что изменится (dry-run)
  python fix_margins.py --apply  # применить изменения в БД (с резервной копией)
"""
import os
import io
import re
import sqlite3
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')

DEFAULT_MARGIN = 40  # проценты наценки для «прочего»

# Порядок важен: первое совпадение выигрывает.
MARGIN_RULES = [
    # аксессуары / амуниция
    (85, ['аксессуар', 'игрушк', 'ошейн', 'миск', 'переноск', 'повод',
          'когтеточ', 'лежан', 'расческ', 'щетк', 'щётк', 'лоток', 'совок',
          'амуниция', 'домик', 'фонтан', 'автокормушк', 'колпак']),
    # наполнители
    (85, ['наполн', 'силикагел', 'сорбент', 'древесн']),
    # препараты и уход
    (85, ['препарат', 'вакцин', 'таблетк', 'капли', 'капл', 'спрей',
          'шампун', 'лосьон', 'мазь', 'гель', 'антгельм', 'от блох',
          'от клещ', 'ветеринар', 'сыворотк', 'глаз', 'ушн']),
    # лакомства
    (45, ['лакомств', 'снек', 'кость', 'кости', 'угощени', 'палочк',
          'жевательн']),
    # влажные корма
    (45, ['пауч', 'влажн', 'консерв', 'рагу', 'желе', 'соус', 'стейк',
          'суп', 'мусс']),
    # премиум-бренды кормов
    (60, ['royal', 'proplan', 'purina', 'hills', 'farmina', 'brit', 'acana',
          'orijen', 'applaws', '1st choice', 'go!', 'now fresh', 'bosch',
          'monge', 'sanabelle', 'leonardo', 'almo', 'grandorf', 'eukanuba',
          'canagan']),
    # сухие / эконом-корма
    (30, ['корм', 'кэт', 'чау', 'pedigree', 'darling', 'дарлинг', 'felix',
          'филикс', 'whiskas', 'вискас', 'perfect fit', 'chappi',
          'наша марка', 'котэ', 'гурмэ', 'пурина']),
]

BRANDS_RE = re.compile(
    r'\b(royal|pro.?plan|purina|hills|farmina|brit|acana|orijen|applaws|'
    r'go|now fresh|bosch|monge|sanabelle|leonardo|almo|grandorf|eukanuba|'
    r'canagan)\b', re.I)


def margin_for(name):
    low = (name or '').lower()
    if BRANDS_RE.search(low):
        return 60
    for margin, kws in MARGIN_RULES:
        for kw in kws:
            if kw in low:
                return margin
    return DEFAULT_MARGIN


def load():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT id, name, retail_price, purchase_price FROM products_1c '
        'WHERE retail_price > 0 OR purchase_price > 0').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def plan():
    stats = {}
    changes = []
    for p in load():
        retail = float(p['retail_price'] or 0)
        purchase = float(p['purchase_price'] or 0)
        m = margin_for(p['name'])
        new_purchase = round(retail / (1 + m / 100.0), 2) if retail > 0 else 0
        need = False
        if retail > 0 and purchase <= 0:
            need = True
        elif retail > 0 and 0 < purchase <= 0.001:
            need = True
        if need:
            stats[m] = stats.get(m, 0) + 1
            changes.append({'id': p['id'], 'name': p['name'],
                            'retail': retail, 'old': purchase,
                            'new': new_purchase, 'margin': m})
    return changes, stats


def main():
    apply = '--apply' in os.sys.argv[1:]
    changes, stats = plan()
    print('Всего товаров для пересчёта приходной цены: %d' % len(changes))
    print('По наценкам:')
    for m in sorted(stats):
        print('   %d%% — %d товаров' % (m, stats[m]))
    print('\nПримеры (первые 15):')
    for ch in changes[:15]:
        print('   %-50s | розница %10.2f | было %9.2f | станет %10.2f | нац.%3d%%'
              % ((ch['name'] or '')[:50], ch['retail'], ch['old'],
                 ch['new'], ch['margin']))
    if not apply:
        print('\nЭто предпросмотр. Чтобы применить: python fix_margins.py --apply')
        return
    # резервная копия
    bak_dir = os.path.join(BASE_DIR, '_1c_backups')
    os.makedirs(bak_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(os.path.join(bak_dir, 'schedule_db_prices_%s.db' % stamp))
    with dst:
        src.backup(dst)
    dst.close(); src.close()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for ch in changes:
        cur.execute('UPDATE products_1c SET purchase_price = ? WHERE id = ?',
                    (ch['new'], ch['id']))
    conn.commit()
    conn.close()
    print('\nПрименено изменений: %d (резервная копия сделана в _1c_backups)'
          % len(changes))


if __name__ == '__main__':
    main()
