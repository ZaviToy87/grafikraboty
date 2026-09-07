@echo off
chcp 65001 >nul
title Анализ продаж и ЗП
cd /d "%~dp0"
echo Запуск анализа продаж, приёмок и зарплат...
python sales_report.py
echo.
pause
