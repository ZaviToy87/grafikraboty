#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронизация данных из 1С (формат EnterpriseData) в базу данных GrafikRaboty

Формат файла: Message_РТ_РТ.xml (выгрузка из 1С:Розница 3.0)
Структура:
  <Body xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.22">
    <Справочник.Номенклатура>...</Справочник.Номенклатура>
    <Справочник.НоменклатураГруппа>...</Справочник.НоменклатураГруппа>
    <Справочник.ШтрихкодыНоменклатуры>...</Справочник.ШтрихкодыНоменклатуры>
    <Справочник.Контрагенты>...</Справочник.Контрагенты>
    <Справочник.Договоры>...</Справочник.Договоры>
    <Справочник.Организации>...</Справочник.Организации>
    <Справочник.Склады>...</Справочник.Склады>
    <Справочник.КассыККМ>...</Справочник.КассыККМ>
    <Справочник.ЕдиницыИзмерения>...</Справочник.ЕдиницыИзмерения>
    <Справочник.СтатьиДДС>...</Справочник.СтатьиДДС>
    <Справочник.ФизическиеЛица>...</Справочник.ФизическиеЛица>
    <Справочник.Пользователи>...</Справочник.Пользователи>
    <Справочник.МаркировкаУпаковки>...</Справочник.МаркировкаУпаковки>
    <Документ.ОтчетОРозничныхПродажах>...</Документ.ОтчетОРозничныхПродажах>
    <Документ.ОприходованиеТоваров>...</Документ.ОприходованиеТоваров>
    <Документ.ПКОРозничнаяВыручка>...</Документ.ПКОРозничнаяВыручка>
    <Документ.ВыемкаДСИзКассыККМ>...</Документ.ВыемкаДСИзКассыККМ>
    <Документ.ИнвентаризацияТоваров>...</Документ.ИнвентаризацияТоваров>
    <Документ.ПКОРасчетыСКонтрагентами>...</Документ.ПКОРасчетыСКонтрагентами>
    <Документ.РКОПрочаяВыдача>...</Документ.РКОПрочаяВыдача>
    <Документ.ВнесениеДСВКассуККМ>...</Документ.ВнесениеДСВКассуККМ>
"""

import os
import re
import json
import sqlite3
import logging
import traceback
from datetime import datetime
from collections import defaultdict

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_1c.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Константы
EXPORT_DIR = r'C:\Users\User\Desktop\Выгрузка 1с'
from app_paths import DB_PATH

# ============================================================
# 1. ПАРСЕР XML (потоковый, для больших файлов)
# ============================================================

class EnterpriseDataParser:
    """Потоковый парсер XML-выгрузки 1С формата EnterpriseData"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.filesize = os.path.getsize(filepath)
        self.body_start = 0
        self.body_end = 0
        
    def find_body_bounds(self):
        """Находит границы тега <Body> в файле"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            chunk = f.read(50000)
            body_tag_start = chunk.find('<Body')
            if body_tag_start == -1:
                raise ValueError("Тег <Body> не найден")
            body_tag_end = chunk.find('>', body_tag_start) + 1
            
            f.seek(self.filesize - 2000)
            tail = f.read(2000)
            body_close = tail.rfind('</Body>')
            if body_close == -1:
                raise ValueError("Тег </Body> не найден")
            
            self.body_start = body_tag_end
            self.body_end = self.filesize - 2000 + body_close
            
    def extract_objects(self, obj_type, max_count=None):
        """
        Извлекает объекты указанного типа из Body.
        obj_type: например 'Справочник.Номенклатура' или 'Документ.ОтчетОРозничныхПродажах'
        """
        if not self.body_start:
            self.find_body_bounds()
        
        objects = []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            f.seek(self.body_start)
            
            # Читаем блоками
            block_size = 10 * 1024 * 1024
            bytes_read = 0
            buffer = ""
            open_tag = f'<{obj_type}'
            close_tag = f'</{obj_type}>'
            
            while bytes_read < (self.body_end - self.body_start):
                to_read = min(block_size, self.body_end - self.body_start - bytes_read)
                chunk = f.read(to_read)
                if not chunk:
                    break
                
                bytes_read += len(chunk)
                buffer += chunk
                
                # Ищем объекты в буфере
                while True:
                    start = buffer.find(open_tag)
                    if start == -1:
                        break
                    
                    # Находим конец открывающего тега
                    tag_end = buffer.find('>', start)
                    if tag_end == -1:
                        break
                    
                    # Ищем закрывающий тег
                    end = buffer.find(close_tag, tag_end)
                    if end == -1:
                        break
                    
                    obj_xml = buffer[start:end + len(close_tag)]
                    objects.append(obj_xml)
                    
                    if max_count and len(objects) >= max_count:
                        return objects
                    
                    # Удаляем обработанное из буфера
                    buffer = buffer[end + len(close_tag):]
                
                # Оставляем в буфере только последние 100KB для контекста
                if len(buffer) > 200000:
                    buffer = buffer[-100000:]
        
        return objects
    
    def extract_all_objects_in_one_pass(self, obj_types):
        """
        Извлекает объекты нескольких типов за один проход по файлу.
        Использует единое регулярное выражение для поиска всех типов сразу.
        
        obj_types: список типов объектов, например ['Справочник.Номенклатура', 'Справочник.ШтрихкодыНоменклатуры']
        Возвращает: dict {obj_type: [list of xml strings]}
        """
        if not self.body_start:
            self.find_body_bounds()
        
        result = {t: [] for t in obj_types}
        
        # Строим единое регулярное выражение для всех типов
        # Экранируем точки в именах типов
        escaped_types = [re.escape(t) for t in obj_types]
        type_pattern = '(' + '|'.join(escaped_types) + ')'
        # Паттерн: <Тип.Объекта ...>...</Тип.Объекта>
        full_pattern = f'<{type_pattern}[^>]*>.*?</\\1>'
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            f.seek(self.body_start)
            
            block_size = 10 * 1024 * 1024
            bytes_read = 0
            buffer = ""
            
            while bytes_read < (self.body_end - self.body_start):
                to_read = min(block_size, self.body_end - self.body_start - bytes_read)
                chunk = f.read(to_read)
                if not chunk:
                    break
                
                bytes_read += len(chunk)
                buffer += chunk
                
                # Ищем все объекты в буфере за один проход
                for match in re.finditer(full_pattern, buffer, re.DOTALL):
                    obj_type = match.group(1)
                    if obj_type in result:
                        result[obj_type].append(match.group(0))
                
                # Оставляем в буфере только последние 200KB для контекста
                # (чуть больше, чтобы не потерять границы объектов)
                if len(buffer) > 400000:
                    buffer = buffer[-200000:]
        
        return result
    
    def extract_all_object_types(self):
        """Извлекает все типы объектов и их количество"""
        if not self.body_start:
            self.find_body_bounds()
        
        object_counts = defaultdict(int)
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            f.seek(self.body_start)
            
            block_size = 10 * 1024 * 1024
            bytes_read = 0
            buffer = ""
            
            while bytes_read < (self.body_end - self.body_start):
                to_read = min(block_size, self.body_end - self.body_start - bytes_read)
                chunk = f.read(to_read)
                if not chunk:
                    break
                
                bytes_read += len(chunk)
                buffer += chunk
                
                # Ищем все теги с точкой
                tags = re.findall(r'<(\w+\.\w+)', buffer)
                for tag in tags:
                    object_counts[tag] += 1
                
                if len(buffer) > 200000:
                    buffer = buffer[-100000:]
        
        return dict(object_counts)


# ============================================================
# 2. ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ XML
# ============================================================

def extract_text(xml, tag):
    """Извлекает текст между тегами"""
    match = re.search(f'<{tag}>(.*?)</{tag}>', xml)
    return match.group(1) if match else None

def extract_guid(xml, tag='Ссылка'):
    """Извлекает GUID из тега"""
    text = extract_text(xml, tag)
    if text and re.match(r'[0-9a-f-]{36}', text):
        return text
    return None

def extract_nested(xml, tag):
    """Извлекает вложенный XML блок"""
    match = re.search(f'<{tag}[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
    return match.group(0) if match else None


def _pick_ref(xml, *tags):
    """Ищет первый вложенный элемент из списка (например Кассир/Продавец/Покупатель)
    и возвращает {'guid': ..., 'name': ...} либо пустые значения."""
    for tag in tags:
        nested = extract_nested(xml, tag)
        if not nested:
            continue
        guid = extract_guid(nested, 'Ссылка')
        name = extract_text(nested, 'Наименование')
        if not name:
            for nt in ('ФИО', 'Представление', 'Имя', 'НаименованиеПолное'):
                name = extract_text(nested, nt)
                if name:
                    break
        if guid or name:
            return {'guid': guid, 'name': name}
    return {'guid': None, 'name': None}

def parse_nomenclature(xml):
    """Парсит Справочник.Номенклатура"""
    data = {
        'guid': extract_guid(xml, 'Ссылка'),
        'code': extract_text(xml, 'КодВПрограмме'),
        'name': extract_text(xml, 'Наименование'),
        'full_name': extract_text(xml, 'НаименованиеПолное'),
        'article': extract_text(xml, 'Артикул'),
        'group_guid': None,
        'group_name': None,
        'unit_guid': None,
        'unit_name': None,
        'is_weight': extract_text(xml, 'Весовой') == 'true',
        'is_set': extract_text(xml, 'ЭтоНабор') == 'true',
        'use_series': extract_text(xml, 'ИспользоватьСерии') == 'true',
        'use_characteristics': extract_text(xml, 'ИспользоватьХарактеристики') == 'true',
        'vat_rate': extract_text(xml, 'СтавкаНДС'),
        'type': extract_text(xml, 'ТипНоменклатуры'),
        'nomenclature_type': extract_text(xml, 'ВидНоменклатуры'),
        'is_deleted': extract_text(xml, 'УдалениеОбъекта') == 'true',
    }
    
    # Извлекаем группу
    group_xml = extract_nested(xml, 'Группа')
    if group_xml:
        data['group_guid'] = extract_guid(group_xml, 'Ссылка')
        data['group_name'] = extract_text(group_xml, 'Наименование')
    
    # Извлекаем единицу измерения
    unit_xml = extract_nested(xml, 'ЕдиницаИзмерения')
    if unit_xml:
        data['unit_guid'] = extract_guid(unit_xml, 'Ссылка')
    
    return data

def parse_barcode(xml):
    """Парсит Справочник.ШтрихкодыНоменклатуры"""
    barcode = extract_text(xml, 'Штрихкод')
    nomenclature_guid = None
    
    # Извлекаем GUID номенклатуры из вложенной структуры
    match = re.search(r'<Ссылка>([0-9a-f-]{36})</Ссылка>', xml)
    if match:
        nomenclature_guid = match.group(1)
    
    return {
        'barcode': barcode,
        'nomenclature_guid': nomenclature_guid
    }

def parse_sale_document(xml):
    """Парсит Документ.ОтчетОРозничныхПродажах"""
    data = {
        'guid': extract_guid(xml, 'Ссылка'),
        'date': extract_text(xml, 'Дата'),
        'number': extract_text(xml, 'Номер'),
        'organization_guid': None,
        'organization_name': None,
        'warehouse_guid': None,
        'warehouse_name': None,
        'total_sum': extract_text(xml, 'Сумма'),
        'currency': extract_text(xml, 'Код'),  # Код валюты
        'taxation': extract_text(xml, 'Налогообложение'),
        'cash_register': extract_text(xml, 'Наименование'),  # Касса ККМ
        'items': []
    }
    
    # Извлекаем организацию
    org_xml = extract_nested(xml, 'Организация')
    if org_xml:
        data['organization_guid'] = extract_guid(org_xml, 'Ссылка')
        data['organization_name'] = extract_text(org_xml, 'Наименование')
    
    # Извлекаем склад
    wh_xml = extract_nested(xml, 'Склад')
    if wh_xml:
        data['warehouse_guid'] = extract_guid(wh_xml, 'Ссылка')
        data['warehouse_name'] = extract_text(wh_xml, 'Наименование')
    
    # Извлекаем товары (табличная часть)
    items_xml = extract_nested(xml, 'ТоварыПродажа')
    if items_xml:
        # Ищем все строки
        rows = re.findall(r'<Строка>(.*?)</Строка>', items_xml, re.DOTALL)
        for row in rows:
            item = {
                'line_number': extract_text(row, 'НомерСтрокиДокумента'),
                'nomenclature_guid': None,
                'nomenclature_name': None,
                'nomenclature_code': None,
                'quantity': extract_text(row, 'Количество'),
                'price': extract_text(row, 'Цена'),
                'sum': extract_text(row, 'Сумма'),
                'unit': extract_text(row, 'Наименование'),  # единица измерения
            }
            
            # Извлекаем номенклатуру
            nom_xml = extract_nested(row, 'Номенклатура')
            if nom_xml:
                item['nomenclature_guid'] = extract_guid(nom_xml, 'Ссылка')
                item['nomenclature_name'] = extract_text(nom_xml, 'Наименование')
                item['nomenclature_code'] = extract_text(nom_xml, 'КодВПрограмме')
            
            data['items'].append(item)

    # Кто продал (кассир/продавец) и кому (покупатель/контрагент), если есть в выгрузке
    seller = _pick_ref(xml, 'Кассир', 'Продавец', 'Ответственный', 'Сотрудник',
                       'Пользователь', 'ФизическоеЛицо', 'Работник')
    buyer = _pick_ref(xml, 'Покупатель', 'Контрагент', 'Клиент')
    data['seller_guid'] = seller['guid']
    data['seller_name'] = seller['name']
    data['buyer_guid'] = buyer['guid']
    data['buyer_name'] = buyer['name']
    
    return data

def parse_receipt_document(xml):
    """Парсит Документ.ОприходованиеТоваров (приемка)"""
    data = {
        'guid': extract_guid(xml, 'Ссылка'),
        'date': extract_text(xml, 'Дата'),
        'number': extract_text(xml, 'Номер'),
        'operation_type': extract_text(xml, 'ВидОперации'),
        'organization_guid': None,
        'organization_name': None,
        'warehouse_guid': None,
        'warehouse_name': None,
        'total_sum': extract_text(xml, 'Сумма'),
        'price_type': extract_text(xml, 'Наименование'),  # Тип цен
        'items': []
    }
    
    # Извлекаем организацию
    org_xml = extract_nested(xml, 'Организация')
    if org_xml:
        data['organization_guid'] = extract_guid(org_xml, 'Ссылка')
        data['organization_name'] = extract_text(org_xml, 'Наименование')
    
    # Извлекаем склад
    wh_xml = extract_nested(xml, 'Склад')
    if wh_xml:
        data['warehouse_guid'] = extract_guid(wh_xml, 'Ссылка')
        data['warehouse_name'] = extract_text(wh_xml, 'Наименование')
    
    # Извлекаем товары
    items_xml = extract_nested(xml, 'Товары')
    if items_xml:
        rows = re.findall(r'<Строка>(.*?)</Строка>', items_xml, re.DOTALL)
        for row in rows:
            item = {
                'nomenclature_guid': None,
                'nomenclature_name': None,
                'nomenclature_code': None,
                'quantity': extract_text(row, 'Количество'),
                'price': extract_text(row, 'Цена'),
                'sum': extract_text(row, 'Сумма'),
            }
            
            nom_xml = extract_nested(row, 'Номенклатура')
            if nom_xml:
                item['nomenclature_guid'] = extract_guid(nom_xml, 'Ссылка')
                item['nomenclature_name'] = extract_text(nom_xml, 'Наименование')
                item['nomenclature_code'] = extract_text(nom_xml, 'КодВПрограмме')
            
            data['items'].append(item)

    # Кто принимал (ответственный/кладовщик) и поставщик, если есть в выгрузке
    who = _pick_ref(xml, 'Ответственный', 'Принял', 'Кладовщик', 'Кассир',
                    'Сотрудник', 'ФизическоеЛицо', 'Работник')
    supplier = _pick_ref(xml, 'Поставщик', 'Контрагент', 'Клиент')
    data['responsible_guid'] = who['guid']
    data['responsible_name'] = who['name']
    data['supplier_guid'] = supplier['guid']
    data['supplier_name'] = supplier['name']
    
    return data

def parse_counterparty(xml):
    """Парсит Справочник.Контрагенты"""
    return {
        'guid': extract_guid(xml, 'Ссылка'),
        'name': extract_text(xml, 'Наименование'),
        'full_name': extract_text(xml, 'НаименованиеПолное'),
        'inn': extract_text(xml, 'ИНН'),
        'kpp': extract_text(xml, 'КПП'),
        'legal_type': extract_text(xml, 'ЮридическоеФизическоеЛицо'),
        'is_individual_entrepreneur': extract_text(xml, 'ИндивидуальныйПредприниматель'),
        'is_self_employed': extract_text(xml, 'Самозанятый'),
        'group_name': None,
        'is_deleted': extract_text(xml, 'УдалениеОбъекта') == 'true',
    }

def parse_organization(xml):
    """Парсит Справочник.Организации"""
    return {
        'guid': extract_guid(xml, 'Ссылка'),
        'name': extract_text(xml, 'Наименование'),
        'short_name': extract_text(xml, 'НаименованиеСокращенное'),
        'full_name': extract_text(xml, 'НаименованиеПолное'),
        'inn': extract_text(xml, 'ИНН'),
        'kpp': extract_text(xml, 'КПП'),
        'legal_type': extract_text(xml, 'ЮридическоеФизическоеЛицо'),
    }


# ============================================================
# 3. СОХРАНЕНИЕ В БАЗУ ДАННЫХ
# ============================================================

class DatabaseSync:
    """Синхронизация данных с SQLite базой"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._init_tables()
        self._ensure_columns()
        self._dedupe_barcodes()
    
    def _init_tables(self):
        """Создает таблицы для данных из 1С, если их нет"""
        
        # Таблица номенклатуры (товары)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_nomenclature (
                guid TEXT PRIMARY KEY,
                code TEXT,
                name TEXT,
                full_name TEXT,
                article TEXT,
                group_guid TEXT,
                group_name TEXT,
                unit_guid TEXT,
                is_weight INTEGER DEFAULT 0,
                is_set INTEGER DEFAULT 0,
                use_series INTEGER DEFAULT 0,
                use_characteristics INTEGER DEFAULT 0,
                vat_rate TEXT,
                type TEXT,
                nomenclature_type TEXT,
                is_deleted INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица штрихкодов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_barcodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT,
                nomenclature_guid TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (nomenclature_guid) REFERENCES sync_nomenclature(guid)
            )
        ''')
        
        # Таблица продаж
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_sales (
                guid TEXT PRIMARY KEY,
                date TIMESTAMP,
                number TEXT,
                organization_guid TEXT,
                organization_name TEXT,
                warehouse_guid TEXT,
                warehouse_name TEXT,
                total_sum REAL,
                currency TEXT,
                taxation TEXT,
                cash_register TEXT,
                seller_guid TEXT,
                seller_name TEXT,
                buyer_guid TEXT,
                buyer_name TEXT,
                raw_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица товаров в продажах
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_guid TEXT,
                line_number INTEGER,
                nomenclature_guid TEXT,
                nomenclature_name TEXT,
                nomenclature_code TEXT,
                quantity REAL,
                price REAL,
                sum REAL,
                unit TEXT,
                FOREIGN KEY (sale_guid) REFERENCES sync_sales(guid),
                FOREIGN KEY (nomenclature_guid) REFERENCES sync_nomenclature(guid)
            )
        ''')
        
        # Таблица приемок (оприходование товаров)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_receipts (
                guid TEXT PRIMARY KEY,
                date TIMESTAMP,
                number TEXT,
                operation_type TEXT,
                organization_guid TEXT,
                organization_name TEXT,
                warehouse_guid TEXT,
                warehouse_name TEXT,
                total_sum REAL,
                price_type TEXT,
                responsible_guid TEXT,
                responsible_name TEXT,
                supplier_guid TEXT,
                supplier_name TEXT,
                raw_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица товаров в приемках
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_guid TEXT,
                nomenclature_guid TEXT,
                nomenclature_name TEXT,
                nomenclature_code TEXT,
                quantity REAL,
                price REAL,
                sum REAL,
                FOREIGN KEY (receipt_guid) REFERENCES sync_receipts(guid),
                FOREIGN KEY (nomenclature_guid) REFERENCES sync_nomenclature(guid)
            )
        ''')
        
        # Таблица контрагентов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_counterparties (
                guid TEXT PRIMARY KEY,
                name TEXT,
                full_name TEXT,
                inn TEXT,
                kpp TEXT,
                legal_type TEXT,
                is_individual_entrepreneur INTEGER DEFAULT 0,
                is_self_employed INTEGER DEFAULT 0,
                group_name TEXT,
                is_deleted INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица организаций
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_organizations (
                guid TEXT PRIMARY KEY,
                name TEXT,
                short_name TEXT,
                full_name TEXT,
                inn TEXT,
                kpp TEXT,
                legal_type TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица складов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_warehouses (
                guid TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для отслеживания синхронизации
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_name TEXT,
                file_size INTEGER,
                objects_count INTEGER,
                status TEXT,
                error TEXT
            )
        ''')
        
        self.conn.commit()
    
    def _ensure_columns(self):
        """Добавляет недостающие колонки в существующие таблицы (для старых БД)."""
        def add_col(table, col, decl):
            cols = [r[1] for r in self.cursor.execute(f'PRAGMA table_info({table})').fetchall()]
            if col not in cols:
                self.cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col} {decl}')
        # sync_sales: продавец/покупатель
        add_col('sync_sales', 'seller_guid', 'TEXT')
        add_col('sync_sales', 'seller_name', 'TEXT')
        add_col('sync_sales', 'buyer_guid', 'TEXT')
        add_col('sync_sales', 'buyer_name', 'TEXT')
        # sync_receipts: ответственный/поставщик
        add_col('sync_receipts', 'responsible_guid', 'TEXT')
        add_col('sync_receipts', 'responsible_name', 'TEXT')
        add_col('sync_receipts', 'supplier_guid', 'TEXT')
        add_col('sync_receipts', 'supplier_name', 'TEXT')
        self.conn.commit()

    def _dedupe_barcodes(self):
        """Убирает возможные дубли штрихкодов (если синхронизация ранее запускалась неоднократно)."""
        self.cursor.execute('''
            DELETE FROM sync_barcodes
            WHERE id NOT IN (
                SELECT MIN(id) FROM sync_barcodes GROUP BY barcode, nomenclature_guid
            )
        ''')
        self.conn.commit()
    
    def save_nomenclature(self, data):
        """Сохраняет номенклатуру"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_nomenclature 
            (guid, code, name, full_name, article, group_guid, group_name, 
             unit_guid, is_weight, is_set, use_series, use_characteristics,
             vat_rate, type, nomenclature_type, is_deleted, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['guid'], data['code'], data['name'], data['full_name'],
            data['article'], data['group_guid'], data['group_name'],
            data['unit_guid'], int(data['is_weight']), int(data['is_set']),
            int(data['use_series']), int(data['use_characteristics']),
            data['vat_rate'], data['type'], data['nomenclature_type'],
            int(data['is_deleted'])
        ))
    
    def save_barcode(self, data):
        """Сохраняет штрихкод"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_barcodes (barcode, nomenclature_guid, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (data['barcode'], data['nomenclature_guid']))
    
    def save_sale(self, data):
        """Сохраняет документ продажи и его товары"""
        # Сохраняем заголовок
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_sales 
            (guid, date, number, organization_guid, organization_name,
             warehouse_guid, warehouse_name, total_sum, currency,
             taxation, cash_register, seller_guid, seller_name,
             buyer_guid, buyer_name, raw_data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['guid'], data['date'], data['number'],
            data['organization_guid'], data['organization_name'],
            data['warehouse_guid'], data['warehouse_name'],
            data['total_sum'], data['currency'],
            data['taxation'], data['cash_register'],
            data.get('seller_guid'), data.get('seller_name'),
            data.get('buyer_guid'), data.get('buyer_name'),
            json.dumps(data, ensure_ascii=False, default=str)
        ))
        
        # Сохраняем товары
        self.cursor.execute('DELETE FROM sync_sale_items WHERE sale_guid = ?', (data['guid'],))
        for item in data['items']:
            self.cursor.execute('''
                INSERT INTO sync_sale_items 
                (sale_guid, line_number, nomenclature_guid, nomenclature_name,
                 nomenclature_code, quantity, price, sum, unit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['guid'], item['line_number'],
                item['nomenclature_guid'], item['nomenclature_name'],
                item['nomenclature_code'], item['quantity'],
                item['price'], item['sum'], item['unit']
            ))
    
    def save_receipt(self, data):
        """Сохраняет документ приемки и его товары"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_receipts 
            (guid, date, number, operation_type, organization_guid, organization_name,
             warehouse_guid, warehouse_name, total_sum, price_type,
             responsible_guid, responsible_name, supplier_guid, supplier_name,
             raw_data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['guid'], data['date'], data['number'],
            data['operation_type'], data['organization_guid'], data['organization_name'],
            data['warehouse_guid'], data['warehouse_name'],
            data['total_sum'], data['price_type'],
            data.get('responsible_guid'), data.get('responsible_name'),
            data.get('supplier_guid'), data.get('supplier_name'),
            json.dumps(data, ensure_ascii=False, default=str)
        ))
        
        self.cursor.execute('DELETE FROM sync_receipt_items WHERE receipt_guid = ?', (data['guid'],))
        for item in data['items']:
            self.cursor.execute('''
                INSERT INTO sync_receipt_items 
                (receipt_guid, nomenclature_guid, nomenclature_name,
                 nomenclature_code, quantity, price, sum)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['guid'], item['nomenclature_guid'],
                item['nomenclature_name'], item['nomenclature_code'],
                item['quantity'], item['price'], item['sum']
            ))
    
    def save_counterparty(self, data):
        """Сохраняет контрагента"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_counterparties
            (guid, name, full_name, inn, kpp, legal_type,
             is_individual_entrepreneur, is_self_employed, group_name,
             is_deleted, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['guid'], data['name'], data['full_name'],
            data['inn'], data['kpp'], data['legal_type'],
            int(data['is_individual_entrepreneur'] == 'true') if data['is_individual_entrepreneur'] else 0,
            int(data['is_self_employed'] == 'true') if data['is_self_employed'] else 0,
            data['group_name'], int(data['is_deleted'])
        ))
    
    def save_organization(self, data):
        """Сохраняет организацию"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_organizations
            (guid, name, short_name, full_name, inn, kpp, legal_type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['guid'], data['name'], data['short_name'],
            data['full_name'], data['inn'], data['kpp'], data['legal_type']
        ))
    
    def log_sync(self, file_name, file_size, objects_count, status, error=None):
        """Логирует синхронизацию"""
        self.cursor.execute('''
            INSERT INTO sync_log (file_name, file_size, objects_count, status, error)
            VALUES (?, ?, ?, ?, ?)
        ''', (file_name, file_size, objects_count, status, error))
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()


# ============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ СИНХРОНИЗАЦИИ
# ============================================================

def sync_from_1c():
    """Основная функция синхронизации"""
    
    # Ищем файл выгрузки
    xml_files = [f for f in os.listdir(EXPORT_DIR) if f.endswith('.xml') and f.startswith('Message_')]
    if not xml_files:
        logger.error(f"Файлы выгрузки не найдены в {EXPORT_DIR}")
        return
    
    xml_file = os.path.join(EXPORT_DIR, xml_files[0])
    logger.info(f"Найден файл выгрузки: {xml_file}")
    logger.info(f"Размер: {os.path.getsize(xml_file) / 1024 / 1024:.2f} MB")
    
    # Инициализируем парсер и БД
    parser = EnterpriseDataParser(xml_file)
    db = DatabaseSync(DB_PATH)
    
    try:
        # Получаем все типы объектов
        logger.info("Анализируем структуру файла...")
        object_types = parser.extract_all_object_types()
        logger.info(f"Найдено типов объектов: {len(object_types)}")
        for obj_type, count in sorted(object_types.items(), key=lambda x: -x[1]):
            logger.info(f"  {obj_type}: {count}")
        
        total_objects = sum(object_types.values())
        
        # Извлекаем все основные типы объектов за один проход по файлу
        logger.info("\n=== ЗАГРУЗКА ВСЕХ ДАННЫХ ИЗ XML (один проход) ===")
        all_data = parser.extract_all_objects_in_one_pass([
            'Справочник.Номенклатура',
            'Справочник.ШтрихкодыНоменклатуры',
            'Документ.ОтчетОРозничныхПродажах',
            'Документ.ОприходованиеТоваров',
            'Справочник.Контрагенты',
            'Справочник.Организации',
            'Справочник.Склады',
        ])
        
        nomenclatures = all_data.get('Справочник.Номенклатура', [])
        barcodes = all_data.get('Справочник.ШтрихкодыНоменклатуры', [])
        sales = all_data.get('Документ.ОтчетОРозничныхПродажах', [])
        receipts = all_data.get('Документ.ОприходованиеТоваров', [])
        counterparties = all_data.get('Справочник.Контрагенты', [])
        organizations = all_data.get('Справочник.Организации', [])
        warehouses = all_data.get('Справочник.Склады', [])
        
        logger.info(f"Загружено: номенклатура={len(nomenclatures)}, штрихкоды={len(barcodes)}, "
                    f"продажи={len(sales)}, приемки={len(receipts)}, "
                    f"контрагенты={len(counterparties)}")
        
        # 1. Синхронизируем номенклатуру (товары)
        logger.info("\n=== СИНХРОНИЗАЦИЯ НОМЕНКЛАТУРЫ ===")
        for i, xml in enumerate(nomenclatures):
            data = parse_nomenclature(xml)
            db.save_nomenclature(data)
            if (i + 1) % 1000 == 0:
                logger.info(f"  Обработано {i+1}/{len(nomenclatures)}")
                db.commit()
        db.commit()
        logger.info(f"Номенклатура синхронизирована: {len(nomenclatures)} записей")
        
        # 2. Синхронизируем штрихкоды
        logger.info("\n=== СИНХРОНИЗАЦИЯ ШТРИХКОДОВ ===")
        for i, xml in enumerate(barcodes):
            data = parse_barcode(xml)
            db.save_barcode(data)
            if (i + 1) % 1000 == 0:
                logger.info(f"  Обработано {i+1}/{len(barcodes)}")
                db.commit()
        db.commit()
        logger.info(f"Штрихкоды синхронизированы: {len(barcodes)} записей")
        
        # 3. Синхронизируем продажи
        logger.info("\n=== СИНХРОНИЗАЦИЯ ПРОДАЖ ===")
        for i, xml in enumerate(sales):
            data = parse_sale_document(xml)
            db.save_sale(data)
            if (i + 1) % 50 == 0:
                logger.info(f"  Обработано {i+1}/{len(sales)}")
                db.commit()
        db.commit()
        logger.info(f"Продажи синхронизированы: {len(sales)} документов")
        
        # 4. Синхронизируем приемки (оприходование)
        logger.info("\n=== СИНХРОНИЗАЦИЯ ПРИЕМОК ===")
        for i, xml in enumerate(receipts):
            data = parse_receipt_document(xml)
            db.save_receipt(data)
            if (i + 1) % 50 == 0:
                logger.info(f"  Обработано {i+1}/{len(receipts)}")
                db.commit()
        db.commit()
        logger.info(f"Приемки синхронизированы: {len(receipts)} документов")
        
        # 5. Синхронизируем контрагентов
        logger.info("\n=== СИНХРОНИЗАЦИЯ КОНТРАГЕНТОВ ===")
        for xml in counterparties:
            data = parse_counterparty(xml)
            db.save_counterparty(data)
        db.commit()
        logger.info(f"Контрагенты синхронизированы: {len(counterparties)} записей")
        
        # 6. Синхронизируем организации
        logger.info("\n=== СИНХРОНИЗАЦИЯ ОРГАНИЗАЦИЙ ===")
        for xml in organizations:
            data = parse_organization(xml)
            db.save_organization(data)
        db.commit()
        logger.info(f"Организации синхронизированы: {len(organizations)} записей")
        
        # 7. Синхронизируем склады
        logger.info("\n=== СИНХРОНИЗАЦИЯ СКЛАДОВ ===")
        for xml in warehouses:
            data = {
                'guid': extract_guid(xml, 'Ссылка'),
                'name': extract_text(xml, 'Наименование'),
                'type': extract_text(xml, 'ТипСклада'),
            }
            db.cursor.execute('''
                INSERT OR REPLACE INTO sync_warehouses (guid, name, type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (data['guid'], data['name'], data['type']))
        db.commit()
        logger.info(f"Склады синхронизированы: {len(warehouses)} записей")
        
        # Логируем успешную синхронизацию
        db.log_sync(xml_files[0], os.path.getsize(xml_file), total_objects, 'success')
        db.commit()
        
        logger.info("\n" + "="*60)
        logger.info("СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        logger.info(f"Всего обработано объектов: {total_objects}")
        logger.info(f"  Номенклатура: {len(nomenclatures)}")
        logger.info(f"  Штрихкоды: {len(barcodes)}")
        logger.info(f"  Продажи: {len(sales)}")
        logger.info(f"  Приемки: {len(receipts)}")
        logger.info(f"  Контрагенты: {len(counterparties)}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        logger.error(traceback.format_exc())
        
        # Логируем ошибку
        db.log_sync(xml_files[0], os.path.getsize(xml_file), 0, 'error', str(e))
        db.commit()
        
    finally:
        db.close()
        logger.info("Соединение с БД закрыто")


# ============================================================
# 5. ИНКРЕМЕНТАЛЬНАЯ ЗАГРУЗКА ОДНОГО ФАЙЛА (дополнение новыми данными)
# ============================================================

def _load_existing_keys(db):
    """Загружает множества уже существующих GUID/пар — для пропуска при повторной загрузке."""
    def colset(table):
        try:
            return {r[0] for r in db.cursor.execute(f'SELECT guid FROM {table}').fetchall()}
        except Exception:
            return set()
    def barcodeset():
        try:
            return {(r[0], r[1]) for r in db.cursor.execute(
                'SELECT barcode, nomenclature_guid FROM sync_barcodes').fetchall()}
        except Exception:
            return set()
    return {
        'nomenclature': colset('sync_nomenclature'),
        'sales': colset('sync_sales'),
        'receipts': colset('sync_receipts'),
        'counterparties': colset('sync_counterparties'),
        'organizations': colset('sync_organizations'),
        'warehouses': colset('sync_warehouses'),
        'barcodes': barcodeset(),
    }


def sync_file(filepath, force=False, full=False):
    """
    Импортирует один файл выгрузки 1С (Message_*.xml).

    По умолчанию (инкрементально) в базу ДОБАВЛЯЮТСЯ только те записи,
    которых ещё нет (по GUID). Уже существующие — пропускаются, поэтому
    повторная загрузка одного и того же файла безопасна.
      force=True — перезаписывать существующие продажи/приёмки/контрагентов;
      full=True  — обновлять и существующую номенклатуру/справочники (включает force).

    Возвращает словарь с итогами.
    """
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f'Файл не найден: {filepath}')
    file_size = os.path.getsize(filepath)
    file_name = os.path.basename(filepath)

    logger.info(f"=== Загрузка файла: {filepath} ({file_size/1024/1024:.1f} MB) ===")

    parser = EnterpriseDataParser(filepath)
    db = DatabaseSync(DB_PATH)

    summary = {'file': file_name, 'file_size': file_size}
    try:
        # Анализ структуры
        object_types = parser.extract_all_object_types()
        total_objects = sum(object_types.values())
        logger.info(f"Типов объектов: {len(object_types)}, всего: {total_objects}")

        # Извлекаем все нужные типы за один проход
        all_data = parser.extract_all_objects_in_one_pass([
            'Справочник.Номенклатура',
            'Справочник.ШтрихкодыНоменклатуры',
            'Документ.ОтчетОРозничныхПродажах',
            'Документ.ОприходованиеТоваров',
            'Справочник.Контрагенты',
            'Справочник.Организации',
            'Справочник.Склады',
        ])

        keys = _load_existing_keys(db)
        stats = {}

        # --- 1. Номенклатура (товары) ---
        inserted = skipped = 0
        for i, xml in enumerate(all_data.get('Справочник.Номенклатура', [])):
            data = parse_nomenclature(xml)
            if data['guid'] in keys['nomenclature'] and not full:
                skipped += 1
                continue
            db.save_nomenclature(data)
            keys['nomenclature'].add(data['guid'])
            inserted += 1
            if (i + 1) % 2000 == 0:
                db.commit()
                logger.info(f"  Номенклатура: обработано {i+1}")
        db.commit()
        stats['nomenclature'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Номенклатура: новых={inserted}, уже было={skipped}")

        # --- 2. Штрихкоды ---
        inserted = skipped = 0
        for i, xml in enumerate(all_data.get('Справочник.ШтрихкодыНоменклатуры', [])):
            data = parse_barcode(xml)
            pair = (data['barcode'], data['nomenclature_guid'])
            if pair in keys['barcodes']:
                skipped += 1
                continue
            db.save_barcode(data)
            keys['barcodes'].add(pair)
            inserted += 1
            if (i + 1) % 2000 == 0:
                db.commit()
                logger.info(f"  Штрихкоды: обработано {i+1}")
        db.commit()
        stats['barcodes'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Штрихкоды: новых={inserted}, уже было={skipped}")

        # --- 3. Продажи ---
        inserted = skipped = 0
        for i, xml in enumerate(all_data.get('Документ.ОтчетОРозничныхПродажах', [])):
            data = parse_sale_document(xml)
            if data['guid'] in keys['sales'] and not force:
                skipped += 1
                continue
            db.save_sale(data)
            keys['sales'].add(data['guid'])
            inserted += 1
            if (i + 1) % 50 == 0:
                db.commit()
                logger.info(f"  Продажи: обработано {i+1}")
        db.commit()
        stats['sales'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Продажи: новых={inserted}, уже было={skipped}")

        # --- 4. Приёмки ---
        inserted = skipped = 0
        for i, xml in enumerate(all_data.get('Документ.ОприходованиеТоваров', [])):
            data = parse_receipt_document(xml)
            if data['guid'] in keys['receipts'] and not force:
                skipped += 1
                continue
            db.save_receipt(data)
            keys['receipts'].add(data['guid'])
            inserted += 1
            if (i + 1) % 50 == 0:
                db.commit()
                logger.info(f"  Приёмки: обработано {i+1}")
        db.commit()
        stats['receipts'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Приёмки: новых={inserted}, уже было={skipped}")

        # --- 5. Контрагенты ---
        inserted = skipped = 0
        for xml in all_data.get('Справочник.Контрагенты', []):
            data = parse_counterparty(xml)
            if data['guid'] in keys['counterparties'] and not force:
                skipped += 1
                continue
            db.save_counterparty(data)
            keys['counterparties'].add(data['guid'])
            inserted += 1
        db.commit()
        stats['counterparties'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Контрагенты: новых={inserted}, уже было={skipped}")

        # --- 6. Организации ---
        inserted = skipped = 0
        for xml in all_data.get('Справочник.Организации', []):
            data = parse_organization(xml)
            if data['guid'] in keys['organizations'] and not force:
                skipped += 1
                continue
            db.save_organization(data)
            keys['organizations'].add(data['guid'])
            inserted += 1
        db.commit()
        stats['organizations'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Организации: новых={inserted}, уже было={skipped}")

        # --- 7. Склады ---
        inserted = skipped = 0
        for xml in all_data.get('Справочник.Склады', []):
            guid = extract_guid(xml, 'Ссылка')
            if guid in keys['warehouses'] and not force:
                skipped += 1
                continue
            data = {
                'guid': guid,
                'name': extract_text(xml, 'Наименование'),
                'type': extract_text(xml, 'ТипСклада'),
            }
            db.cursor.execute('''
                INSERT OR REPLACE INTO sync_warehouses (guid, name, type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (data['guid'], data['name'], data['type']))
            keys['warehouses'].add(guid)
            inserted += 1
        db.commit()
        stats['warehouses'] = {'new': inserted, 'skipped': skipped}
        logger.info(f"Склады: новых={inserted}, уже было={skipped}")

        summary['stats'] = stats
        summary['total_objects'] = total_objects

        db.log_sync(file_name, file_size, total_objects, 'success')
        db.commit()
        logger.info("=== ЗАГРУЗКА УСПЕШНО ЗАВЕРШЕНА ===")
        return summary

    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        logger.error(traceback.format_exc())
        try:
            db.log_sync(file_name, file_size, 0, 'error', str(e)[:2000])
            db.commit()
        except Exception:
            pass
        raise

    finally:
        db.close()
        logger.info("Соединение с БД закрыто")

def find_export_files(folder):
    """Возвращает список файлов Message_*.xml в папке (по убыванию времени изменения)."""
    if not os.path.isdir(folder):
        return []
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if f.lower().endswith('.xml') and f.lower().startswith('message_')]
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files


def _print_summary(summary):
    print("\n" + "=" * 60)
    print(f"ФАЙЛ: {summary.get('file')} ({summary.get('file_size', 0) / 1024 / 1024:.1f} MB)")
    print("=" * 60)
    labels = {
        'nomenclature': 'Товары (номенклатура)',
        'barcodes': 'Штрихкоды',
        'sales': 'Продажи (документы)',
        'receipts': 'Приёмки (документы)',
        'counterparties': 'Контрагенты',
        'organizations': 'Организации',
        'warehouses': 'Склады',
    }
    stats = summary.get('stats', {})
    if not stats:
        print("  (нет данных)")
        return
    for key, label in labels.items():
        s = stats.get(key)
        if not s:
            continue
        print(f"  {label}: ДОБАВЛЕНО новых = {s['new']}, уже было в базе = {s['skipped']}")
    print("=" * 60)


if __name__ == '__main__':
    import sys as _sys
    args = [a for a in _sys.argv[1:]]
    flags = set()
    targets = []
    for a in args:
        if a in ('--force', '--full', '--no-backup'):
            flags.add(a)
        else:
            targets.append(a)

    force = '--force' in flags
    full = '--full' in flags

    candidates = []
    if targets:
        for t in targets:
            if os.path.isdir(t):
                candidates.extend(find_export_files(t))
            elif os.path.isfile(t):
                candidates.append(t)
    if not candidates:
        # По умолчанию: папка выгрузки, затем папка uploads проекта
        for folder in (EXPORT_DIR, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')):
            candidates.extend(find_export_files(folder))
            if candidates:
                break
    if not candidates:
        print("Файлы выгрузки (Message_*.xml) не найдены.")
        print("Укажите путь к файлу или папке, например:")
        print('  python sync_1c.py "C:\\путь\\Message_РТ_РТ.xml"')
        _sys.exit(1)

    for fpath in candidates:
        print(f"\n>>> Загружаю: {fpath}")
        try:
            summary = sync_file(fpath, force=force, full=full)
            _print_summary(summary)
        except Exception as e:
            print(f"!!! Ошибка при загрузке {fpath}: {e}")
            _sys.exit(2)

