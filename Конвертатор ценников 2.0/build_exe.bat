@echo off
cd /d "%~dp0"

REM Создаём и активируем виртуальное окружение, если его нет
if not exist ".venv\Scripts\activate" (
    echo Виртуального окружения нет — создаю .venv
    python -m venv .venv
)

call .venv\Scripts\activate

REM Устанавливаем зависимости
python -m pip install --upgrade pip
python -m pip install pyinstaller openpyxl

REM Собираем exe (указываем имя скрипта app.py)
pyinstaller --onefile --noconsole --name "КонвертаторЦенников 2.0" "app.py"

if %ERRORLEVEL% neq 0 (
    echo Ошибка сборки. Уберите --noconsole для отладки или присылайте вывод.
    pause
    exit /b %ERRORLEVEL%
)

echo Сборка завершена. Файл: dist\КонвертаторЦенников 2.0.exe
pause
