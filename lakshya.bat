@echo off
setlocal
set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo Virtual environment not found. Please run setup first.
    exit /b 1
)
"%VENV_PYTHON%" "%~dp0lakshya.py" %*
