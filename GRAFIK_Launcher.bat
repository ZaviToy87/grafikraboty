@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM Запуск в свёрнутом виде: чёрное окно консоли не отвлекает, приложение в трее/окне
if "%~1"=="" ( start /min cmd /c "%~f0" run & exit /b )

set PY=
if exist ".venv1\Scripts\python.exe" set PY=.venv1\Scripts\python.exe
if not defined PY if exist "python.exe" set PY=python.exe
if not defined PY set PY=python

REM Однократная установка зависимостей при первом запуске (если нет venv)
REM --user чтобы не писать в Program Files (иначе "Access is denied")
if not exist ".venv1\Scripts\python.exe" if not exist ".installed_deps" (
    echo Установка зависимостей при первом запуске...
    if exist "requirements-core.txt" (
        "%PY%" -m pip install --user -r requirements-core.txt -q 2>nul
    ) else (
        "%PY%" -m pip install --user -r requirements.txt -q 2>nul
    )
    if not errorlevel 1 echo. > .installed_deps
    echo Пробуем установить окно приложения ^(pywebview^)... может не установиться на части ПК.
    "%PY%" -m pip install --user pywebview -q 2>nul
)

"%PY%" main_launcher.py
if errorlevel 1 pause
