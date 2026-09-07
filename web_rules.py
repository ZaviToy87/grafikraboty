# -*- coding: utf-8 -*-
"""
web_rules.py — страница «Правила и методичка» + API и ручной запуск напоминаний.
"""
import sqlite3
from flask import Blueprint, render_template, jsonify, request, session, redirect

import company_rules as cr

rules_bp = Blueprint('rules', __name__)

_seeded = [False]


def _ensure():
    if not _seeded[0]:
        try:
            cr.seed_docs()
            _seeded[0] = True
        except Exception:
            pass


def _require_login():
    if 'user_id' not in session:
        return None
    return session['user_id']


@rules_bp.route('/rules')
def rules_page():
    uid = _require_login()
    if uid is None:
        return redirect('/login')
    _ensure()
    try:
        docs = cr.get_docs()
    except Exception as e:
        docs = [{'title': 'Ошибка', 'body': str(e)}]
    is_admin = session.get('role') == 'admin'
    return render_template('rules.html', docs=docs, is_admin=is_admin,
                           user_name=session.get('full_name'))


@rules_bp.route('/api/rules')
def rules_api():
    if _require_login() is None:
        return jsonify({'error': 'Не авторизован'}), 401
    _ensure()
    try:
        docs = cr.get_docs()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'docs': docs})


@rules_bp.route('/api/rules/remind', methods=['POST'])
def rules_remind():
    if _require_login() is None:
        return jsonify({'error': 'Не авторизован'}), 401
    if session.get('role') != 'admin':
        return jsonify({'error': 'Только для администратора'}), 403
    try:
        sent = cr.send_today_shift_reminder(force=True)
        return jsonify({'status': 'ok', 'sent': sent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
