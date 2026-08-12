# -*- coding: utf-8 -*-
"""Тест API аналитики 1С"""
import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Логинимся как сотрудник (без верификации)
login_data = json.dumps({'username': 'валерия', 'password': 'pass123'}).encode()
req = urllib.request.Request('http://127.0.0.1:8080/login', data=login_data, headers={'Content-Type': 'application/json'})
resp = opener.open(req)
print('Login:', resp.status, resp.reason)
login_result = json.loads(resp.read())
print('Login result:', json.dumps(login_result, ensure_ascii=False))
print()

# Проверяем страницу аналитики
resp = opener.open('http://127.0.0.1:8080/sync-1c/analytics')
html = resp.read().decode()
print('Page status:', resp.status)
print('Page length:', len(html))
print('Has analytics:', 'Аналитика 1С' in html)
print('Has Chart.js:', 'Chart' in html)
print('Has tabs:', 'tab-overview' in html and 'tab-margin' in html)
print()

# Проверяем API аналитики
resp = opener.open('http://127.0.0.1:8080/api/sync-1c/analytics?days=30')
data = json.loads(resp.read())
s = data.get('summary',{})
print('=== API Analytics Summary ===')
print(f'Days: {s.get("days")}')
print(f'Sales: {s.get("sales",{}).get("doc_count")} docs, {s.get("sales",{}).get("total_sum")} sum')
print(f'Receipts: {s.get("receipts",{}).get("doc_count")} docs, {s.get("receipts",{}).get("total_sum")} sum')
print(f'Gross profit: {s.get("gross_profit")}')
print(f'Margin: {s.get("margin_percent")}%')
print(f'Products in trade: {s.get("products_in_trade")}')
print(f'Stock items: {s.get("stock_items_count")}')
print(f'Daily data points: {len(data.get("daily_data",[]))}')
print(f'Margin products: {len(data.get("margin_products",[]))}')
print(f'Liquidity products: {len(data.get("liquidity_products",[]))}')
print(f'Stock products: {len(data.get("stock_products",[]))}')
print(f'Revision products: {len(data.get("revision_products",[]))}')
