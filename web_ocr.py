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

    result = {'items': [], 'text': '', 'fields': {}, 'error': '', 'count': 0}
    if request.method == 'POST':
        files = request.files.getlist('files')
        files = [f for f in files if f and f.filename]
        if not files:
            result['error'] = 'Файлы не выбраны'
        else:
            os.makedirs(UPLOADS, exist_ok=True)
            combined = []
            combined_fields = {}
            for f in files:
                name = '%s_%s' % (int(time.time()), uuid.uuid4().hex[:6])
                ext = os.path.splitext(f.filename)[1] or '.jpg'
                path = os.path.join(UPLOADS, '_ocr_%s%s' % (name, ext))
                f.save(path)
                try:
                    text = ocr.ocr_image(path)
                    fields = ocr.extract_fields(text) if text else {}
                    item = {'name': f.filename, 'text': text}
                    result['items'].append(item)
                    if text:
                        combined.append('===== %s =====\n%s' % (f.filename, text))
                        for k, v in fields.items():
                            if k != 'text' and v:
                                combined_fields.setdefault(k, v)
                finally:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            result['count'] = len(result['items'])
            result['text'] = '\n\n'.join(combined)
            result['fields'] = combined_fields
            if not result['items']:
                result['error'] = 'Файлы не обработаны'
    return render_template('ocr.html', result=result)
