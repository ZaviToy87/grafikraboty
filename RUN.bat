@echo off
title GrafikRaboty Server
cd /d "%~dp0"
chcp 65001 >nul

echo.
echo ============================================================
echo    GRAFIKRABOTY - SERVER
echo ============================================================
echo.

set PYTHON=python
if exist "%~dp0python\python.exe" set PYTHON=%~dp0python\python.exe

echo Python: %PYTHON%
%PYTHON% --version
echo.

echo Starting server...
echo Local: http://127.0.0.1:8080
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

%PYTHON% main_launcher.py

pause
