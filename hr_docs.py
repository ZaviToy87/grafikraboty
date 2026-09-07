# -*- coding: utf-8 -*-
"""
hr_docs.py — генерация кадровых документов ООО «КАКИЕ ЛЮДИ» (ВетГид) в Word.

Комплект нового сотрудника (2026):
  * Анкета сотрудника
  * Договор о полной индивидуальной материальной ответственности
  * Агентский договор
  * Договор о неразглашении конфиденциальной информации
  * Памятка с учётными данными для входа в программу
Образцы журналов для магазина/ветаптеки:
  * Журнал учёта температуры и влажности (холодильники)
  * График уборки помещений
  * Журнал списания/брака
"""
import os
import io
import json
import re
import zipfile
from datetime import datetime

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = 'Times New Roman'
DOCS_DIR = os.path.join(BASE_DIR, 'docs')


def load_requisites():
    path = os.path.join(BASE_DIR, 'company_requisites.json')
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _base_ctx(emp):
    req = load_requisites()
    org = req.get('organization', {})
    ctx = dict(org)
    ctx['year'] = req.get('docs_year', 2026)
    ctx.update(emp or {})
    return ctx


def new_doc(landscape=False):
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.6)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(1.5)
    if landscape:
        sec.orientation = 1  # landscape
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    st = doc.styles['Normal']
    st.font.name = FONT
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    return doc


def P(doc, text='', bold=False, center=False, right=False, size=None,
      space_after=4, underline=False, italic=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.12
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif right:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.underline = underline
    if size:
        r.font.size = Pt(size)
    return p


def line(doc, label, width=50):
    """Строка с подчёркиванием для заполнения."""
    P(doc, '%s %s' % (label, '_' * width), space_after=6)


def value_or_blank(v, width=42):
    v = (v or '').strip()
    return v if v else '_' * width


def fill(text, ctx):
    import re as _re
    def rep(m):
        return str(ctx.get(m.group(1), ''))
    return _re.sub(r'\{([A-Za-z0-9_]+)\}', rep, text)


def org_header(doc, ctx, city='Самара'):
    P(doc, ctx.get('full_name', ''), center=True, bold=True, size=13)
    P(doc, ctx.get('actual_address', '') or ctx.get('legal_address', ''),
      center=True, size=10)
    if ctx.get('phone') or ctx.get('email'):
        P(doc, ('%s  %s' % (ctx.get('phone', ''), ctx.get('email', ''))).strip(),
          center=True, size=10)
    P(doc, 'ИНН %s, КПП %s, ОГРН %s' % (value_or_blank(ctx.get('inn'), 14),
                                         value_or_blank(ctx.get('kpp'), 14),
                                         value_or_blank(ctx.get('ogrn'), 15)),
      center=True, size=10)
    P(doc, '', space_after=6)


def build_anketa(emp, path):
    """Анкета сотрудника."""
    ctx = _base_ctx(emp)
    doc = new_doc()
    P(doc, 'АНКЕТА СОТРУДНИКА', center=True, bold=True, size=14, space_after=2)
    P(doc, ctx.get('short_name', '') + ' (бренд %s)' % ctx.get('brand', ''),
      center=True, size=11, space_after=8)
    P(doc, 'Заполняется при приёме на работу.', size=10, italic=True)
    fields = [
        ('Фамилия', 'surname'), ('Имя', 'name'), ('Отчество', 'patronymic'),
        ('Дата рождения', 'birth_date'), ('Телефон', 'phone'),
        ('Адрес регистрации', 'address_registration'),
        ('Адрес проживания', 'address_residence'),
        ('Серия и номер паспорта', 'passport'),
        ('Кем выдан паспорт', 'passport_by'),
        ('Дата выдачи', 'passport_date'), ('Код подразделения', 'passport_code'),
        ('ИНН', 'inn'), ('СНИЛС', 'snils'),
        ('Должность', 'position'), ('Дата начала работы', 'date_start'),
        ('График работы', 'work_schedule'),
        ('Заработная плата (оклад/порядок)', 'salary_scheme'),
    ]
    for label, key in fields:
        line(doc, label + ':', 60)
    P(doc, '', space_after=4)
    P(doc, 'С правилами внутреннего трудового распорядка, должностной '
           'инструкцией, правилами охраны труда и пожарной безопасности, '
           'Методичкой сотрудника ознакомлен(а):', size=11)
    P(doc, 'Подпись ____________________ / %s /  %s г.'
      % (value_or_blank(ctx.get('fio'), 34),
         value_or_blank(ctx.get('date_start', ctx.get('year', '')), 18)), size=11)
    doc.save(path)
    return path


def build_material_contract(emp, path):
    """Договор о полной индивидуальной материальной ответственности."""
    ctx = _base_ctx(emp)
    doc = new_doc()
    org_header(doc, ctx)
    P(doc, 'ДОГОВОР', center=True, bold=True, size=13, space_after=0)
    P(doc, 'о полной индивидуальной материальной ответственности работника',
      center=True, bold=True, size=13, space_after=6)
    P(doc, fill('г. Самара\n{date_contract}', ctx), space_after=6)
    intro = fill('{short_name} (далее — «Работодатель»), в лице '
                 '{director_position} {director_fio}, действующего на основании '
                 '{director_basis}, с одной стороны, и гражданин(ка) РФ {fio} '
                 '(далее — «Работник»), с другой стороны, заключили настоящий '
                 'договор о нижеследующем.', ctx)
    P(doc, intro)
    P(doc, '1. ПРЕДМЕТ ДОГОВОРА', bold=True)
    P(doc, '1.1. Работник, занимающий должность «{position}» '
           '(принимает на себя полную индивидуальную материальную '
           'ответственность за недостачу вверенного ему Работодателем '
           'имущества, а также за ущерб, возникший у Работодателя в '
           'результате возмещения им ущерба иным лицам.'.format(**ctx))
    P(doc, '1.2. Настоящий договор заключён в соответствии со ст. 242–244 '
           'Трудового кодекса РФ и Перечнем должностей и работ, замещаемых '
           'или выполняемых работниками, с которыми работодатель может '
           'заключать письменные договоры о полной индивидуальной '
           'материальной ответственности, утверждённым Постановлением '
           'Минтруда России от 31.12.2002 № 85.')
    P(doc, '2. ОБЯЗАННОСТИ РАБОТНИКА', bold=True)
    P(doc, '2.1. Бережно относиться к переданному ему имуществу '
           'Работодателя и принимать меры к предотвращению ущерба.')
    P(doc, '2.2. Своевременно сообщать Работодателю обо всех '
           'обстоятельствах, угрожающих обеспечению сохранности вверенного '
           'имущества.')
    P(doc, '2.3. Вести учёт, своевременно и в установленном порядке '
           'составлять и представлять отчёты о движении и остатках '
           'вверенного имущества (товаров, денежных средств).')
    P(doc, '2.4. Участвовать в проведении инвентаризаций, ревизий и иных '
           'проверок сохранности имущества.')
    P(doc, '3. ОБЯЗАННОСТИ РАБОТОДАТЕЛЯ', bold=True)
    P(doc, '3.1. Создавать Работнику условия, необходимые для нормальной '
           'работы и обеспечения полной сохранности вверенного имущества.')
    P(doc, '3.2. Своевременно проводить инвентаризации и ревизии, '
           'фиксировать их результаты.')
    P(doc, '3.3. Знакомить Работника с действующим законодательством о '
           'материальной ответственности.')
    P(doc, '4. ПОРЯДОК ОПРЕДЕЛЕНИЯ РАЗМЕРА УЩЕРБА', bold=True)
    P(doc, '4.1. Размер ущерба определяется по фактическим потерям на '
           'основании данных бухгалтерского учёта (ст. 246 ТК РФ). При '
           'недостаче имущества размер ущерба определяется из рыночной '
           'стоины на день причинения ущерба, но не ниже балансовой '
           'стоимости.')
    P(doc, '5. ОТВЕТСТВЕННОСТЬ СТОРОН', bold=True)
    P(doc, '5.1. Работник несёт полную материальную ответственность за '
           'недостачу вверенного имущества в размере причинённого ущерба '
           '(ст. 242, 243 ТК РФ).')
    P(doc, '5.2. Причинение ущерба не при каких-либо обстоятельствах не '
           'освобождает Работника от обязанности возместить ущерб, если '
           'доказана его вина.')
    P(doc, '6. ПРОЧИЕ УСЛОВИЯ', bold=True)
    P(doc, '6.1. Договор вступает в силу с момента подписания и действует '
           'в течение всего периода работы Работника с вверенным ему '
           'имуществом.')
    P(doc, '6.2. Договор составлен в двух экземплярах, имеющих одинаковую '
           'юридическую силу: один — у Работодателя, второй — у Работника.')
    P(doc, '', space_after=6)
    P(doc, '7. АДРЕСА И ПОДПИСИ СТОРОН', bold=True)
    P(doc, 'Работодатель:', bold=True)
    P(doc, '%s\nОГРН %s, ИНН %s, КПП %s\n%s\n%s'
      % (ctx.get('full_name', ''), ctx.get('ogrn', ''), ctx.get('inn', ''),
         ctx.get('kpp', ''), ctx.get('legal_address', ''),
         ctx.get('actual_address', '')), size=11)
    P(doc, 'Банк: %s, БИК %s, р/с %s, к/с %s'
      % (ctx.get('bank_name', ''), ctx.get('bank_bik', ''),
         ctx.get('bank_account', ''), ctx.get('bank_corr_account', '')),
      size=11)
    P(doc, fill('{director_position}: ________________ /{director_fio}/', ctx),
      size=11)
    P(doc, '', space_after=4)
    P(doc, 'Работник:', bold=True)
    P(doc, '{fio}\nПаспорт: {passport}, выдан {passport_by} {passport_date}\n'
           'Адрес: {address_registration}'.format(**ctx), size=11)
    P(doc, 'Подпись: ________________', size=11)
    doc.save(path)
    return path


def build_agent_contract(emp, path):
    """Агентский договор с сотрудником (продавцом-агентом)."""
    ctx = _base_ctx(emp)
    doc = new_doc()
    org_header(doc, ctx)
    P(doc, 'АГЕНТСКИЙ ДОГОВОР № ______', center=True, bold=True, size=13,
      space_after=0)
    P(doc, 'на совершение действий от имени Принципала', center=True,
      bold=True, size=12, space_after=6)
    P(doc, fill('г. Самара\n{date_contract}', ctx), space_after=6)
    intro = fill('{short_name} (далее — «Принципал»), в лице '
                 '{director_position} {director_fio}, действующего на '
                 'основании {director_basis}, с одной стороны, и {fio} '
                 '(далее — «Агент»), с другой стороны, заключили настоящий '
                 'договор о нижеследующем:', ctx)
    P(doc, intro)
    P(doc, '1. ПРЕДМЕТ ДОГОВОРА', bold=True)
    P(doc, '1.1. По настоящему договору Агент обязуется от имени и за счёт '
           'Принципала совершать юридические и иные действия по продаже '
           'товаров зоомагазина и ветаптеки (бренд «{brand}»), приёму '
           'денежных средств от покупателей, ведению кассовых операций и '
           'предоставлению покупателям информации о товарах.'.format(**ctx))
    P(doc, '1.2. Агент действует на территории г. Самары и '
           'Самарской области.')
    P(doc, '1.3. Полномочия Агента подтверждаются доверенностью, '
           'выдаваемой Принципалом.')
    P(doc, '2. ПРАВА И ОБЯЗАННОСТИ АГЕНТА', bold=True)
    P(doc, '2.1. Агент обязуется:')
    P(doc, '— лично совершать действия, предусмотренные п. 1.1 договора;')
    P(doc, '— соблюдать правила внутреннего распорядка, Методичку '
           'сотрудника и инструкции Принципала;')
    P(doc, '— обеспечивать сохранность товара и денежных средств, '
           'своевременно сдавать выручку;')
    P(doc, '— не разглашать конфиденциальную информацию Принципала.')
    P(doc, '2.2. Агент вправе получать вознаграждение в порядке, '
           'предусмотренном разделом 3 договора.')
    P(doc, '3. ВОЗНАГРАЖДЕНИЕ АГЕНТА', bold=True)
    P(doc, '3.1. Вознаграждение Агента устанавливается сторонами в '
           'размере, согласованном в дополнительном соглашении / листе '
           'согласования (процент от выручки или фиксированная оплата за '
           'смену по действующей у Принципала схеме мотивации).')
    P(doc, '3.2. Вознаграждение выплачивается не реже одного раза в месяц '
           'в порядке, установленном локальными актами Принципала.')
    P(doc, '4. ОТЧЁТНОСТЬ АГЕНТА', bold=True)
    P(doc, '4.1. Агент предоставляет Принципалу отчёт о выполненной работе '
           'в порядке и сроки, установленные Принципалом (по итогам '
           'каждой смены).')
    P(doc, '5. ОТВЕТСТВЕННОСТЬ СТОРОН', bold=True)
    P(doc, '5.1. За неисполнение или ненадлежащее исполнение обязанностей '
           'по договору стороны несут ответственность в соответствии с '
           'законодательством РФ.')
    P(doc, '5.2. Агент несёт материальную ответственность за утрату '
           '(недостачу) вверенных товарно-материальных ценностей в '
           'порядке ст. 242–244 ТК РФ и отдельного договора о полной '
           'материальной ответственности.')
    P(doc, '6. СРОК ДЕЙСТВИЯ И ПРОЧИЕ УСЛОВИЯ', bold=True)
    P(doc, '6.1. Договор заключён в соответствии с главой 52 ГК РФ '
           '(ст. 1005–1011) и действует с даты подписания по 31.12.%s г.'
           % ctx.get('year', 2026))
    P(doc, '6.2. Договор может быть расторгнут по основаниям, '
           'предусмотренным законодательством РФ.')
    P(doc, '6.3. Договор составлен в двух экземплярах, имеющих одинаковую '
           'юридическую силу.')
    P(doc, '', space_after=4)
    P(doc, '7. ПОДПИСИ СТОРОН', bold=True)
    P(doc, 'Принципал: %s' % ctx.get('full_name', ''), size=11)
    P(doc, fill('{director_position}: _______________ /{director_fio}/', ctx),
      size=11)
    P(doc, 'Агент: {fio}'.format(**ctx), size=11)
    P(doc, 'Подпись: ________________  Паспорт: {passport}'.format(**ctx),
      size=11)
    doc.save(path)
    return path


def build_nda_contract(emp, path):
    """Договор о неразглашении конфиденциальной информации."""
    ctx = _base_ctx(emp)
    doc = new_doc()
    org_header(doc, ctx)
    P(doc, 'ДОГОВОР № ______', center=True, bold=True, size=13, space_after=0)
    P(doc, 'о неразглашении конфиденциальной информации '
           '(коммерческой тайны)', center=True, bold=True, size=12,
      space_after=6)
    P(doc, fill('г. Самара\n{date_contract}', ctx), space_after=6)
    intro = fill('{short_name} (далее — «Компания»), в лице '
                 '{director_position} {director_fio}, действующего на '
                 'основании {director_basis}, с одной стороны, и {fio} '
                 '(далее — «Сотрудник»), с другой стороны, заключили '
                 'настоящий договор о нижеследующем:', ctx)
    P(doc, intro)
    P(doc, '1. ОПРЕДЕЛЕНИЯ И ПРЕДМЕТ', bold=True)
    P(doc, '1.1. Конфиденциальная информация (КИ) — сведения, составляющие '
           'коммерческую тайну Компании, а также иные сведения, ставшие '
           'известными Сотруднику в связи с выполнением трудовых/'
           'гражданско-правовых обязанностей: о покупателях и '
           'контрагентах, ценах и условиях закупок, выручке, учётных '
           'данных и паролях, внутренних документах, методиках продаж.')
    P(doc, '1.2. Сотрудник обязуется не разглашать КИ третьим лицам и не '
           'использовать её в личных целях в период действия договора и в '
           'течение 3 (трёх) лет после его прекращения.')
    P(doc, '2. ОБЯЗАННОСТИ СТОРОН', bold=True)
    P(doc, '2.1. Компания обязана:')
    P(doc, '— ознакомить Сотрудника с перечнем сведений, составляющих '
           'коммерческую тайну;')
    P(doc, '— обеспечить соблюдение режима коммерческой тайны.')
    P(doc, '2.2. Сотрудник обязан:')
    P(doc, '— не передавать КИ третьим лицам без письменного согласия '
           'Компании;')
    P(doc, '— не использовать КИ в личных целях и не допускать её '
           'разглашения, включая публикации в сети Интернет и мессенджерах;')
    P(doc, '— соблюдать режим доступа к учётным записям программы, не '
           'передавать свой пароль другим лицам;')
    P(doc, '— незамедлительно сообщать Компании о фактах возможного '
           'разглашения КИ.')
    P(doc, '3. ОТВЕТСТВЕННОСТЬ', bold=True)
    P(doc, '3.1. За разглашение КИ Сотрудник несёт ответственность в '
           'соответствии с законодательством РФ, включая возмещение '
           'причинённых убытков.')
    P(doc, '3.2. Отношения по охране коммерческой тайны регулируются '
           'Федеральным законом от 29.07.2004 № 98-ФЗ «О коммерческой '
           'тайне», ст. 1465–1472 ГК РФ, а в части персональных данных — '
           'Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных '
           'данных».')
    P(doc, '4. СРОК ДЕЙСТВИЯ', bold=True)
    P(doc, '4.1. Договор вступает в силу с момента подписания и действует '
           'в течение всего периода работы Сотрудника, а обязательства о '
           'неразглашении КИ — в течение 3 (трёх) лет после прекращения '
           'договора.')
    P(doc, '4.2. Договор составлен в двух экземплярах, имеющих одинаковую '
           'юридическую силу.')
    P(doc, '', space_after=4)
    P(doc, '5. ПОДПИСИ СТОРОН', bold=True)
    P(doc, 'Компания: %s' % ctx.get('full_name', ''), size=11)
    P(doc, fill('{director_position}: _______________ /{director_fio}/', ctx),
      size=11)
    P(doc, 'Сотрудник: {fio}'.format(**ctx), size=11)
    P(doc, 'Подпись: ________________', size=11)
    doc.save(path)
    return path


def build_access_memo(emp, path):
    """Памятка сотрудника: учётные данные и первые шаги."""
    ctx = _base_ctx(emp)
    doc = new_doc()
    P(doc, 'ПАМЯТКА СОТРУДНИКА (учётные данные и первые шаги)',
      center=True, bold=True, size=13, space_after=6)
    P(doc, ctx.get('short_name', '') + ' — бренд ' + ctx.get('brand', ''),
      center=True, size=11, space_after=8)
    P(doc, fill('Сотрудник: {fio}', ctx))
    P(doc, fill('Должность: {position}', ctx))
    P(doc, fill('Дата начала работы: {date_start}', ctx))
    P(doc, '', space_after=4)
    P(doc, 'ДОСТУП К ПРОГРАММЕ «ВЕТГИД ГРАФИК»:', bold=True)
    P(doc, fill('Адрес входа: {site_url}', ctx))
    P(doc, fill('Логин: {login}', ctx))
    P(doc, fill('Пароль: {password}', ctx))
    P(doc, '', space_after=4)
    P(doc, 'ВАЖНО:', bold=True)
    P(doc, '• Никому не сообщайте свой пароль. За разглашение пароля и '
           'доступа предусмотрена ответственность по договору о '
           'неразглашении.')
    P(doc, '• Перед первой сменой прочитайте «Методичку сотрудника» и '
           '«Правила магазина» (раздел «📖 Правила и методичка» в '
           'программе).')
    P(doc, '• В начале смены откройте кассовую смену в программе, в конце '
           '— закройте и сдайте выручку по инструкции.')
    P(doc, '• При возникновении вопросов обращайтесь к руководству.')
    P(doc, '', space_after=4)
    P(doc, 'Ознакомлен(а) и обязуюсь соблюдать:')
    P(doc, 'Подпись ____________________ / {fio} / {date_start}'
      .format(**ctx), size=11)
    doc.save(path)
    return path


# ============================================================
# Образцы журналов для магазина и ветаптеки
# ============================================================
def _make_table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        cell = t.cell(0, j)
        cell.text = h
        for par in cell.paragraphs:
            for r in par.runs:
                r.bold = True
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            t.cell(i + 1, j).text = val
    return t


def _journal_blank_rows(n, first_col_shift=1):
    return [[''] * first_col_shift + [''] for _ in range(n)]


def build_temperature_journal(path, rows=31):
    doc = new_doc(landscape=True)
    P(doc, 'ЖУРНАЛ', center=True, bold=True, size=14, space_after=0)
    P(doc, 'учёта температуры и влажности в холодильном оборудовании',
      center=True, bold=True, size=12, space_after=6)
    P(doc, 'ООО «КАКИЕ ЛЮДИ» (ВетГид). Холодильное оборудование магазина '
           'и ветаптеки.', size=10)
    P(doc, 'Норма: температура в холодильниках +2…+6 °C, в морозильных '
           'камерах −18 °C и ниже. Замеры проводятся 2 раза в день.',
      size=10, italic=True)
    headers = ['Дата', 'Время', 'Холодильник №1, °C', 'Холодильник №2, °C',
               'Морозильная камера, °C', 'Влажность, %',
               'Отклонение/примечания', 'Подпись']
    rows_data = [[''] * len(headers) for _ in range(rows)]
    _make_table(doc, headers, rows_data)
    doc.save(path)
    return path


def build_cleaning_schedule(path, rows=31):
    doc = new_doc()
    P(doc, 'ГРАФИК УБОРКИ ПОМЕЩЕНИЙ', center=True, bold=True, size=14,
      space_after=2)
    P(doc, 'ООО «КАКИЕ ЛЮДИ» (ВетГид). Месяц: ____________ 2026 г.',
      center=True, size=11, space_after=6)
    P(doc, 'Уборка выполняется ежедневно по «Правилам магазина»; '
           'генеральная уборка — по графику.', size=10, italic=True)
    headers = ['Дата', 'Торговый зал (пол)', 'Полки/витрины',
               'Санузел', 'Служебное помещение', 'Подпись']
    rows_data = [[''] * len(headers) for _ in range(rows)]
    _make_table(doc, headers, rows_data)
    doc.save(path)
    return path


def build_writeoff_journal(path, rows=31):
    doc = new_doc()
    P(doc, 'ЖУРНАЛ СПИСАНИЯ И БРАКА ТОВАРА', center=True, bold=True,
      size=14, space_after=6)
    P(doc, 'ООО «КАКИЕ ЛЮДИ» (ВетГид).', center=True, size=11)
    P(doc, 'Записи вносятся при выявлении брака, повреждения упаковки, '
           'просрочки товара.', size=10, italic=True)
    headers = ['Дата', 'Наименование товара', 'Штрихкод/артикул',
               'Кол-во', 'Причина списания', 'Номер акта', 'Подпись']
    rows_data = [[''] * len(headers) for _ in range(rows)]
    _make_table(doc, headers, rows_data)
    doc.save(path)
    return path


def build_journals(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    files = [
        build_temperature_journal(os.path.join(
            out_dir, 'Журнал_температуры_и_влажности.docx')),
        build_cleaning_schedule(os.path.join(
            out_dir, 'График_уборки_помещений.docx')),
        build_writeoff_journal(os.path.join(
            out_dir, 'Журнал_списания_и_брака.docx')),
    ]
    return files


# ============================================================
# Методичка и правила (входят в пакет каждого сотрудника)
# ============================================================
def build_methodichka(emp, path):
    return _text_doc(path, 'МЕТОДИЧКА СОТРУДНИКА',
                     os.path.join(DOCS_DIR, 'МЕТОДИЧКА_сотрудника.txt'))


def build_pravila(emp, path):
    return _text_doc(path, 'ПРАВИЛА МАГАЗИНА',
                     os.path.join(DOCS_DIR, 'Правила_магазина.txt'))


def _text_doc(path, title, src_path):
    ctx = _base_ctx({})
    doc = new_doc()
    P(doc, ctx.get('short_name', '') + ' — бренд ' + ctx.get('brand', ''),
      center=True, size=10)
    P(doc, title, center=True, bold=True, size=14, space_after=6)
    try:
        with io.open(src_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
    except Exception:
        lines = []
    import re as _re
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        bold = bool(_re.match(r'^\s*(\d+\.|[-—•*]?\s*[А-ЯЁA-Z][А-ЯЁA-Z ]{6,})', s)
                     or _re.match(r'^(КАК|НЕ|ДОЛЖЕН|ОБЯЗАН|ПРАВИЛ|МЕТОД)', s,
                                  _re.I))
        P(doc, s, bold=bold, size=11, space_after=3)
    P(doc, '', space_after=2)
    P(doc, 'С документом ознакомлен(а): ______________ / ____________ / 20__ г.',
      size=10)
    doc.save(path)
    return path


# ============================================================
# Пакет документов сотрудника
# ============================================================
# (kind, метка_для_файла, функция-генератор)
DOC_BUILDERS = [
    ('anketa', '01_Анкета_сотрудника', build_anketa),
    ('material', '02_Договор_материальная_ответственность',
     build_material_contract),
    ('agent', '03_Агентский_договор', build_agent_contract),
    ('nda', '04_Договор_о_неразглашении', build_nda_contract),
    ('memo', '05_Памятка_учётные_данные', build_access_memo),
    ('methodichka', '06_Методичка_сотрудника', build_methodichka),
    ('pravila', '07_Правила_магазина', build_pravila),
]
DOC_LABELS = {k: l for k, l, _ in DOC_BUILDERS}

def sanitize(name):
    return re.sub(r'[\\/:*?"<>|]+', '_', str(name or '').strip()) or 'документы'


def default_employee():
    """Пустой (чистовой) профиль сотрудника — заполняется при приёме."""
    return {
        'fio': '', 'surname': '', 'name': '', 'patronymic': '',
        'birth_date': '', 'phone': '', 'passport': '',
        'passport_by': '', 'passport_date': '', 'passport_code': '',
        'address_registration': '', 'address_residence': '',
        'inn': '', 'snils': '', 'position': 'Продавец-кассир',
        'date_start': '', 'date_contract': '«___» ____________ 2026 г.',
        'work_schedule': '', 'salary_scheme': '',
        'login': '', 'password': '', 'site_url': 'http://<адрес сервера>:8080',
    }


def build_employee_kit(emp, out_dir):
    """Формирует комплект документов нового сотрудника и возвращает пути."""
    ctx = dict(default_employee())
    ctx.update(emp or {})
    os.makedirs(out_dir, exist_ok=True)
    name = sanitize(ctx.get('fio') or 'новый_сотрудник')
    files = []
    for kind, label, fn in DOC_BUILDERS:
        p = os.path.join(out_dir, '%s_%s.docx' % (label, name))
        fn(ctx, p)
        files.append(p)
    return files


def build_kit_zip(emp, zip_path):
    """Формирует пакет и упаковывает его в zip-архив."""
    tmp = zip_path + '.tmp_dir'
    files = build_employee_kit(emp, tmp)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.basename(f))
    for f in files:
        try:
            os.remove(f)
        except OSError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    return zip_path





