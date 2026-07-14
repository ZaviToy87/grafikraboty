@echo off
setlocal enableextensions enabledelayedexpansion

REM Try to activate local venv if exists
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

REM Run the converter
python convert.py %*

REM Keep window open if double-clicked
if "%CMDCMDLINE%"=="" (
  echo.
  echo Press any key to exit...
  pause >nul
)
