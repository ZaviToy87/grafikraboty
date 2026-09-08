# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from flask import Flask
import web_orders, web_expiry

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE, 'templates'))
app.secret_key = 'x'
app.register_blueprint(web_orders.orders_bp)
app.register_blueprint(web_expiry.expiry_bp)

print('URL MAP:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'orders' in rule.rule or 'expiry' in rule.rule:
        print(' ', rule.rule, sorted(rule.methods))

with app.test_client() as c:
    with c.session_transaction() as s:
        s['user_id'] = 3; s['role'] = 'employee'
        s['username'] = 'ольга'; s['full_name'] = 'Ольга Сотрудник'
    for path in ('/orders', '/expiry'):
        r = c.get(path)
        data = r.get_data(as_text=True)
        print(path, r.status_code, 'len', len(data), 'title?',
              ('Заявки' in data or 'Сроки' in data))
        if r.status_code != 200:
            print(data[:800])
