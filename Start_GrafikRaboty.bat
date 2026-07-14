@echo off
chcp 65001 >nul
cd /d "%~dp0"
title График работы

set "PYTHON="
if exist "%~dp0python\python.exe" set "PYTHON=%~dp0python\python.exe"
if not defined PYTHON set "PYTHON=python"

"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Не найден Python. Сейчас откроется страница загрузки.
    echo   Установите Python и обязательно отметьте "Add Python to PATH".
    echo.
    start https://www.python.org/downloads/
    echo   Нажмите любую клавишу после установки Python...
    pause >nul
    "%PYTHON%" --version >nul 2>&1
    if errorlevel 1 (
        echo   Python по-прежнему не найден. Добавьте Python в PATH и запустите снова.
        pause
        exit /b 1
    )
)

echo Проверка и установка библиотек (один раз)...
"%PYTHON%" check_and_install.py
if errorlevel 1 (
    echo Попытка установить из requirements.txt...
    "%PYTHON%" -m pip install -r requirements.txt -q
)

echo.
echo Запуск графика работы...
echo.
"%PYTHON%" main_launcher.py

echo.
pause
