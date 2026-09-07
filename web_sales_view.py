# -*- coding: utf-8 -*-
"""
web_sales_view.py — «Аналитика продаж» (этап 1+2): по дням и по сотрудникам.
Привязка к графику/сменам + сверка касса vs 1С.
"""
import os
from flask import Blueprint, render_template, session, redirect, request

import sales_analytics as sa

sales_view_bp = Blueprint('sales_view', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _admin():
    return session.get('role') == 'admin'


@sales_view_bp.route('/analytics-sales')
def sales_view_page():
    if 'user_id' not in session:
        return redirect('/login')
    if not _admin():
        return 'Доступ только для администратора', 403
    start = (request.args.get('start') or '').strip() or None
    end = (request.args.get('end') or '').strip() or None
    db = os.path.join(BASE_DIR, 'schedule.db')
    cfg = sa.load_config()
    a = sa.SalesAnalytics(db, cfg)
    rep = a.analyze(start=start, end=end)
    # работники по именам для фильтра-подсказки
    return render_template('sales_view.html', rep=rep, start=start or '',
                           end=end or '')
