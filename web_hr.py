# -*- coding: utf-8 -*-
"""
web_hr.py — кадровый модуль: приём сотрудника + автоматический пакет документов.

Админ заводит сотрудника (или выбирает существующего), заполняет данные —
система сама:
  * создаёт учётную запись (логин/пароль генерируются),
  * формирует комплект Word-документов (.docx) + zip для скачивания и печати.
"""
import os
import io
import re
import json
import hashlib
import secrets
import sqlite3
import string
from datetime import datetime

from flask import (Blueprint, render_template, jsonify, request, session,
                   redirect, send_file)

import hr_docs as H

hr_bp = Blueprint('hr', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')
PKG_DIR = os.path.join(BASE_DIR, 'hr_packages')

FIELDS = [
    'fio', 'surname', 'name', 'patronymic', 'birth_date', 'phone',
    'passport', 'passport_by', 'passport_date', 'passport_code',
    'address_registration', 'address_residence', 'inn', 'snils',
    'position', 'date_start', 'work_schedule', 'salary_scheme',
    'login', 'password', 'site_url',
]


def _db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _db()
    c.execute('''
        CREATE TABLE IF NOT EXISTS hr_employee_data (
            user_id INTEGER PRIMARY KEY,
            data_json TEXT,
            zip_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.commit()
    c.close()


def _admin():
    return session.get('role') == 'admin'


def _hash_password(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()


def gen_password(length=8):
    alpha = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alpha) for _ in range(length))


def _user_list():
    c = _db()
    rows = c.execute('SELECT id, username, full_name, role FROM users '
                     'ORDER BY id').fetchall()
    c.close()
    return [dict(r) for r in rows]


def _save_package(user_id, data):
    os.makedirs(PKG_DIR, exist_ok=True)
    name = H.sanitize(data.get('fio') or ('user_%s' % user_id))
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_path = os.path.join(PKG_DIR, 'HR_%s_%s_%s.zip' % (user_id, name, stamp))
    H.build_kit_zip(data, zip_path)
    c = _db()
    c.execute('INSERT OR REPLACE INTO hr_employee_data (user_id, data_json, '
              'zip_name) VALUES (?, ?, ?)',
              (user_id, json.dumps(data, ensure_ascii=False), os.path.basename(zip_path)))
    c.commit()
    c.close()
    return zip_path


# ---------- страницы и API ----------
@hr_bp.route('/admin/hr')
def hr_page():
    if 'user_id' not in session:
        return redirect('/login')
    if not _admin():
        return 'Доступ только для администратора', 403
    _ensure()
    return render_template('hr.html', users=_user_list(), fields=FIELDS)


@hr_bp.route('/api/hr/generate', methods=['POST'])
def hr_generate():
    if 'user_id' not in session or not _admin():
        return jsonify({'error': 'Доступ только для администратора'}), 403
    _ensure()
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get('username') or '').strip().lower()
    full_name = (data.get('full_name') or '').strip()
    password = (data.get('password') or '').strip()

    c = _db()
    if not username:
        return jsonify({'error': 'Не указан логин'}), 400

    row = c.execute('SELECT id FROM users WHERE username = ?',
                    (username,)).fetchone()
    if row:
        uid = row['id']
    else:
        if not password:
            password = gen_password()
        if not full_name:
            full_name = username
        cur = c.execute(
            'INSERT INTO users (username, password_hash, role, full_name) '
            'VALUES (?, ?, ?, ?)',
            (username, _hash_password(password), 'employee', full_name))
        uid = cur.lastrowid
    c.close()

    fields = {f: (data.get(f) or '') for f in FIELDS}
    if not fields.get('fio') and full_name:
        fields['fio'] = full_name
    fields['login'] = username
    fields['password'] = password or 'смотри в памятке'
    fields['site_url'] = fields.get('site_url') or \
        ('http://%s:8080' % (request.host.split(':')[0] if request.host else 'localhost'))
    if not fields.get('date_contract'):
        fields['date_contract'] = '«___» ____________ 2026 г.'

    try:
        zip_path = _save_package(uid, fields)
    except Exception as e:
        return jsonify({'error': 'Ошибка формирования документов: %s' % e}), 500

    return jsonify({
        'status': 'ok', 'user_id': uid, 'username': username,
        'password': password,
        'zip_name': os.path.basename(zip_path),
        'download_url': '/api/hr/package/%d?n=%s' % (uid, os.path.basename(zip_path)),
    })


@hr_bp.route('/api/hr/package/<int:user_id>')
def hr_download(user_id):
    if 'user_id' not in session or not _admin():
        return 'Доступ только для администратора', 403
    _ensure()
    c = _db()
    row = c.execute('SELECT zip_name FROM hr_employee_data WHERE user_id = ?',
                    (user_id,)).fetchone()
    c.close()
    if not row or not row['zip_name']:
        return 'Пакет не найден', 404
    path = os.path.join(PKG_DIR, row['zip_name'])
    if not os.path.isfile(path):
        return 'Файл не найден', 404
    return send_file(path, as_attachment=True,
                     download_name=row['zip_name'])
