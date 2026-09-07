# -*- coding: utf-8 -*-
"""
web_hr.py — кадровый модуль «Пул сотрудников».

Возможности (админ):
  * список текущих сотрудников (создаётся из пользователей программы);
  * редактирование данных сотрудника (паспорт, адреса, телефон, ИНН/СНИЛС…);
  * создание нового сотрудника: учётная запись + пароль автоматически;
  * формирование полного пакета документов (zip) или отдельных документов;
  * хранение дополнительных файлов сотрудника (подписанные договоры, сканы…).
"""
import os
import io
import re
import json
import shutil
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
FILES_DIR = os.path.join(BASE_DIR, 'hr_files')

# Поля, которые храним по каждому сотруднику
HR_COLS = ['user_id', 'username', 'password', 'fio', 'surname', 'name',
           'patronymic', 'birth_date', 'phone', 'passport', 'passport_by',
           'passport_date', 'passport_code', 'address_registration',
           'address_residence', 'inn', 'snils', 'position', 'date_start',
           'work_schedule', 'salary_scheme', 'login', 'site_url', 'notes']

FILE_CATEGORIES = ['договор', 'паспорт', 'снилс', 'диплом', 'прочее']

# Обязательные данные для формирования документов
REQUIRED_FIELDS = [
    ('fio', 'ФИО'), ('position', 'Должность'),
    ('birth_date', 'Дата рождения'), ('phone', 'Телефон'),
    ('passport', 'Паспорт (серия и номер)'), ('passport_by', 'Кем выдан паспорт'),
    ('passport_date', 'Дата выдачи паспорта'),
    ('passport_code', 'Код подразделения'),
    ('address_registration', 'Адрес регистрации'),
    ('address_residence', 'Адрес проживания'),
]


def missing_required(emp):
    return [label for key, label in REQUIRED_FIELDS
            if not (emp.get(key) or '').strip()]


def _db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _db()
    c.execute('''
        CREATE TABLE IF NOT EXISTS hr_employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            password TEXT,
            fio TEXT, surname TEXT, name TEXT, patronymic TEXT,
            birth_date TEXT, phone TEXT,
            passport TEXT, passport_by TEXT, passport_date TEXT,
            passport_code TEXT,
            address_registration TEXT, address_residence TEXT,
            inn TEXT, snils TEXT,
            position TEXT, date_start TEXT,
            work_schedule TEXT, salary_scheme TEXT,
            login TEXT, site_url TEXT, notes TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS hr_employee_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            category TEXT,
            orig_name TEXT,
            stored_name TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.commit()
    c.close()


def _admin():
    return session.get('role') == 'admin'


def _owner_ok(emp):
    """Сотрудник может работать только со СВОИМИ документами."""
    if _admin():
        return True
    if not emp:
        return False
    uid = session.get('user_id')
    return bool(uid) and str(emp.get('user_id')) == str(uid)


def _hash_password(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()


def gen_password(length=8):
    alpha = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alpha) for _ in range(length))


def _seed_from_users():
    """Один раз: заносим существующих пользователей в пул сотрудников."""
    _ensure()
    c = _db()
    users = c.execute('SELECT id, username, full_name, role FROM users '
                      'ORDER BY id').fetchall()
    for u in users:
        row = c.execute('SELECT id FROM hr_employee WHERE user_id = ?',
                        (u['id'],)).fetchone()
        if not row:
            c.execute('INSERT INTO hr_employee (user_id, username, fio, '
                      'position, active) VALUES (?, ?, ?, ?, 1)',
                      (u['id'], u['username'],
                       u['full_name'] or u['username'], 'Сотрудник'))
    c.commit()
    c.close()


def _row_emp(emp_id):
    c = _db()
    row = c.execute('SELECT * FROM hr_employee WHERE id = ?',
                    (emp_id,)).fetchone()
    c.close()
    return dict(row) if row else None


def _emp_doc_ctx(emp_id):
    emp = _row_emp(emp_id)
    if not emp:
        return None
    ctx = dict(H.default_employee())
    for k in list(ctx.keys()):
        if emp.get(k):
            ctx[k] = emp[k]
    if not ctx.get('fio') and emp.get('fio'):
        ctx['fio'] = emp['fio']
    ctx['login'] = emp.get('login') or emp.get('username') or ''
    return ctx


def _gen_emp_file(emp_id, kind):
    """Генерирует отдельный документ, возвращает (путь, имя файла)."""
    ctx = _emp_doc_ctx(emp_id)
    if not ctx:
        return None, None
    builder = next((fn for k, lbl, fn in H.DOC_BUILDERS if k == kind), None)
    if not builder:
        return None, None
    label = H.DOC_LABELS.get(kind, kind)
    name = H.sanitize(ctx.get('fio') or ('сотрудник_%s' % emp_id))
    os.makedirs(PKG_DIR, exist_ok=True)
    path = os.path.join(PKG_DIR, 'doc_%s_%s_%s.docx' % (emp_id, kind, name))
    builder(ctx, path)
    return path, '%s_%s.docx' % (label, name)


# ---------- страница ----------
@hr_bp.route('/admin/hr')
def hr_page():
    if 'user_id' not in session:
        return redirect('/login')
    if not _admin():
        return 'Доступ только для администратора', 403
    _ensure()
    employees = _employee_rows()
    for e in employees:
        e['missing'] = missing_required(e)
    return render_template('hr.html', employees=employees,
                           doc_builders=[{'kind': k, 'label': l}
                                         for k, l, _ in H.DOC_BUILDERS],
                           categories=FILE_CATEGORIES)


# ---------- сохранение сотрудника ----------
@hr_bp.route('/api/hr/employee/save', methods=['POST'])
def hr_save():
    if not _admin():
        return jsonify({'error': 'Доступ только для администратора'}), 403
    _ensure()
    body = request.get_json(force=True, silent=True) or {}
    emp_id = body.get('id')
    username = (body.get('username') or '').strip().lower()
    password = (body.get('password') or '').strip()
    fio = (body.get('fio') or body.get('full_name') or '').strip()

    c = _db()
    user_id = None
    created_user = False
    if username:
        u = c.execute('SELECT id FROM users WHERE username = ?',
                      (username,)).fetchone()
        if u:
            user_id = u['id']
        else:
            if not password:
                password = gen_password()
                created_user = True
            cur = c.execute(
                'INSERT INTO users (username, password_hash, role, full_name) '
                'VALUES (?, ?, ?, ?)',
                (username, _hash_password(password), 'employee',
                 fio or username))
            user_id = cur.lastrowid
            created_user = True
    # пересоздание пароля по явному запросу
    if body.get('reset_password') and user_id:
        if not password:
            password = gen_password()
        c.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                  (_hash_password(password), user_id))

    vals = {col: (body.get(col) or '') for col in HR_COLS}
    vals['user_id'] = user_id if user_id is not None else vals.get('user_id')
    vals['username'] = username
    vals['login'] = username
    vals['password'] = password if (password or created_user) else ''
    vals['fio'] = fio or vals.get('fio')
    if not vals.get('position'):
        vals['position'] = 'Продавец-кассир'
    if not vals.get('site_url'):
        host = request.host.split(':')[0] if request.host else 'localhost'
        vals['site_url'] = 'http://%s:8080' % host

    if emp_id:
        sets = ', '.join('%s = ?' % col for col in HR_COLS)
        c.execute('UPDATE hr_employee SET %s, updated_at = CURRENT_TIMESTAMP '
                  'WHERE id = ?' % sets, [vals[col] for col in HR_COLS] + [emp_id])
    else:
        cur = c.execute(
            'INSERT INTO hr_employee (%s) VALUES (%s)'
            % (', '.join(HR_COLS), ', '.join('?' for _ in HR_COLS)),
            [vals[col] for col in HR_COLS])
        emp_id = cur.lastrowid
    c.commit()
    c.close()
    return jsonify({'status': 'ok', 'id': emp_id,
                    'password': password if (password or created_user) else '',
                    'created_user': created_user})


def _employee_rows():
    _seed_from_users()
    c = _db()
    rows = c.execute('''SELECT h.*, (SELECT COUNT(*) FROM hr_employee_files f
                        WHERE f.employee_id = h.id) AS files_count
                        FROM hr_employee h
                        ORDER BY h.active DESC, h.fio''').fetchall()
    c.close()
    return [dict(r) for r in rows]


# ---------- документы сотрудника ----------
@hr_bp.route('/api/hr/employee/<int:emp_id>/doc/<kind>')
def hr_doc(emp_id, kind):
    emp = _row_emp(emp_id)
    if not _owner_ok(emp):
        return 'Нет доступа к документам этого сотрудника', 403
    missing = missing_required(emp)
    if missing:
        return ('Сначала заполните обязательные данные: %s' % ', '.join(missing),
                400)
    path, name = _gen_emp_file(emp_id, kind)
    if not path:
        return 'Документ не найден', 404
    return send_file(path, as_attachment=True, download_name=name)


@hr_bp.route('/api/hr/employee/<int:emp_id>/package')
def hr_package(emp_id):
    emp = _row_emp(emp_id)
    if not _owner_ok(emp):
        return 'Нет доступа к документам этого сотрудника', 403
    missing = missing_required(emp)
    if missing:
        return ('Нельзя сформировать пакет — сначала заполните обязательные '
                'данные: %s' % ', '.join(missing), 400)
    ctx = _emp_doc_ctx(emp_id)
    if not ctx:
        return 'Сотрудник не найден', 404
    os.makedirs(PKG_DIR, exist_ok=True)
    name = H.sanitize(ctx.get('fio') or ('сотрудник_%s' % emp_id))
    zip_path = os.path.join(PKG_DIR, 'Пакет_%s_2026.zip' % name)
    try:
        H.build_kit_zip(ctx, zip_path)
        return send_file(zip_path, as_attachment=True,
                         download_name='Пакет_%s_2026.zip' % name)
    finally:
        try:
            if os.path.isfile(zip_path):
                os.remove(zip_path)
        except OSError:
            pass


# ---------- файлы сотрудника ----------
@hr_bp.route('/api/hr/employee/<int:emp_id>/files', methods=['GET'])
def hr_files_list(emp_id):
    if not _owner_ok(_row_emp(emp_id)):
        return jsonify({'error': 'Нет доступа'}), 403
    c = _db()
    rows = c.execute('SELECT * FROM hr_employee_files WHERE employee_id = ? '
                     'ORDER BY id DESC', (emp_id,)).fetchall()
    c.close()
    return jsonify({'files': [dict(r) for r in rows]})


@hr_bp.route('/api/hr/employee/<int:emp_id>/files', methods=['POST'])
def hr_files_upload(emp_id):
    if not _admin():
        return jsonify({'error': 'Нет доступа'}), 403
    if not _row_emp(emp_id):
        return jsonify({'error': 'Сотрудник не найден'}), 404
    up = request.files.get('file')
    if not up or not up.filename:
        return jsonify({'error': 'Файл не выбран'}), 400
    category = (request.form.get('category') or 'прочее').strip()
    orig = os.path.basename(up.filename)
    folder = os.path.join(FILES_DIR, str(emp_id))
    os.makedirs(folder, exist_ok=True)
    stored = '%s_%s' % (datetime.now().strftime('%Y%m%d%H%M%S'),
                        re.sub(r'[\\/:*?"<>|]', '_', orig))
    up.save(os.path.join(folder, stored))
    c = _db()
    cur = c.execute(
        'INSERT INTO hr_employee_files (employee_id, category, orig_name, '
        'stored_name) VALUES (?, ?, ?, ?)',
        (emp_id, category, orig, stored))
    c.commit()
    fid = cur.lastrowid
    c.close()
    return jsonify({'status': 'ok', 'id': fid, 'name': orig})


@hr_bp.route('/api/hr/employee/<int:emp_id>/file/<int:fid>')
def hr_file_download(emp_id, fid):
    if not _owner_ok(_row_emp(emp_id)):
        return 'Нет доступа', 403
    c = _db()
    row = c.execute('SELECT * FROM hr_employee_files WHERE id = ? AND '
                    'employee_id = ?', (fid, emp_id)).fetchone()
    c.close()
    if not row:
        return 'Файл не найден', 404
    path = os.path.join(FILES_DIR, str(emp_id), row['stored_name'])
    if not os.path.isfile(path):
        return 'Файл не найден', 404
    return send_file(path, as_attachment=True, download_name=row['orig_name'])


@hr_bp.route('/api/hr/employee/<int:emp_id>/file/<int:fid>', methods=['DELETE'])
def hr_file_delete(emp_id, fid):
    if not _admin():
        return jsonify({'error': 'Нет доступа'}), 403
    c = _db()
    row = c.execute('SELECT * FROM hr_employee_files WHERE id = ? AND '
                    'employee_id = ?', (fid, emp_id)).fetchone()
    if row:
        try:
            os.remove(os.path.join(FILES_DIR, str(emp_id), row['stored_name']))
        except OSError:
            pass
        c.execute('DELETE FROM hr_employee_files WHERE id = ?', (fid,))
        c.commit()
    c.close()
    return jsonify({'status': 'ok'})


# ---------- «Мои документы» для сотрудника ----------
@hr_bp.route('/my-docs')
def my_docs_page():
    if 'user_id' not in session:
        return redirect('/login')
    _ensure()
    uid = session.get('user_id')
    c = _db()
    emp = c.execute('SELECT * FROM hr_employee WHERE user_id = ?', (uid,)
                    ).fetchone()
    c.close()
    emp = dict(emp) if emp else None
    missing = missing_required(emp) if emp else []
    return render_template('mydocs.html', emp=emp, missing=missing,
                           doc_builders=[{'kind': k, 'label': l}
                                         for k, l, _ in H.DOC_BUILDERS])



