@echo off
echo.
echo  =====================================================
echo   Lakshya Installer — lak·shya (Sanskrit: Goal)
echo  =====================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install Python 3.8+ first.
    pause
    exit /b 1
)

echo  [1/3] Creating virtual environment...
python -m venv "%~dp0venv"

echo  [2/3] Installing dependencies...
"%~dp0venv\Scripts\pip.exe" install -q click rich

echo  [3/3] Installing 'lakshya' as a global command...
"%~dp0venv\Scripts\pip.exe" install -q -e "%~dp0."

echo.
echo  =====================================================
echo   Done! You can now run:  lakshya
echo   (Make sure your venv is activated first)
echo  =====================================================
echo.
echo   Activate venv with:
echo   . venv\Scripts\Activate.ps1
echo.
pause
