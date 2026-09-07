# -*- coding: utf-8 -*-
"""
web_ocr.py — «Анализатор сканов»: распознавание текста с фото/сканов.
"""
import os
import io
import time
import uuid
from flask import Blueprint, render_template, request, session, redirect

import ocr_analyzer as ocr

ocr_bp = Blueprint('ocr', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE_DIR, 'uploads')


def _admin():
    return session.get('role') == 'admin'


@ocr_bp.route('/ocr', methods=['GET', 'POST'])
def ocr_page():
    if 'user_id' not in session:
        return redirect('/login')
    if not _admin():
        return 'Доступ только для администратора', 403

    result = {'text': '', 'fields': {}, 'error': '', 'name': ''}
    if request.method == 'POST':
        f = request.files.get('file')
        if not f or not f.filename:
            result['error'] = 'Файл не выбран'
        else:
            os.makedirs(UPLOADS, exist_ok=True)
            name = '%s_%s' % (int(time.time()), uuid.uuid4().hex[:6])
            ext = os.path.splitext(f.filename)[1] or '.jpg'
            path = os.path.join(UPLOADS, '_ocr_%s%s' % (name, ext))
            f.save(path)
            try:
                text = ocr.ocr_image(path)
                if not text:
                    result['error'] = ('Текст не распознан (OCR не смог прочитать '
                                       'изображение). Попробуйте более чёткий скан.')
                result['text'] = text
                result['fields'] = ocr.extract_fields(text) or {}
                result['name'] = f.filename
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass
    return render_template('ocr.html', result=result)
