@echo off
chcp 65001 >nul
title Загрузка выгрузки 1С в базу
cd /d "%~dp0"

echo ============================================================
echo  Загрузка файла выгрузки 1С (Message_*.xml) в базу GrafikRaboty
echo  Данные ДОПОЛНЯЮТ базу: добавляются только те записи,
echo  которых ещё нет (продажи, приёмки, товары, контрагенты).
echo ============================================================
echo.

if "%~1"=="" (
    echo Перетащите файл Message_*.xml на этот ярлык
    echo или введите путь к файлу вручную:
    set /p FILEPATH=Путь к файлу: 
) else (
    set "FILEPATH=%~1"
)

if defined FILEPATH (
    python sync_1c.py "%FILEPATH%"
) else (
    python sync_1c.py
)

echo.
echo Готово. Закрыть окно? 
pause
