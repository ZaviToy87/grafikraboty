# -*- coding: utf-8 -*-
"""Формирование документов и журналов ООО «КАКИЕ ЛЮДИ» (ВетГид).

Примеры:
  python make_docs.py                       # чистые бланки комплекта + журналы
  python make_docs.py --json data.json      # комплект с данными сотрудника
  python make_docs.py --journals-only       # только журналы/образцы
"""
import os
import io
import sys
import json
import shutil

import hr_docs as H

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    emp_json = None
    journals_only = False
    out_dir = os.path.join(BASE_DIR, 'documents_out')
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--json' and i + 1 < len(argv):
            emp_json = argv[i + 1]
            i += 1
        elif a == '--out' and i + 1 < len(argv):
            out_dir = argv[i + 1]
            i += 1
        elif a == '--journals-only':
            journals_only = True
        i += 1

    emp = {}
    if emp_json:
        with io.open(emp_json, 'r', encoding='utf-8') as f:
            emp = json.load(f)

    if journals_only or not emp:
        jdir = os.path.join(out_dir, 'Журналы_и_образцы')
        files = H.build_journals(jdir)
        print('Сформированы журналы:')
        for f in files:
            print('  ', f)

    if journals_only:
        return 0

    # пакет документов сотрудника
    if emp:
        name = H.sanitize(emp.get('fio') or 'сотрудник')
    else:
        name = 'чистовые_бланки'
    pdir = os.path.join(out_dir, 'Пакет_%s_%s' % (name, '2026'))
    files = H.build_employee_kit(emp, pdir)
    zip_path = os.path.join(out_dir, 'Пакет_%s_2026.zip' % name)
    H.build_kit_zip(emp, zip_path)
    print('Пакет документов:')
    for f in files:
        print('  ', f)
    print('Архив:', zip_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
