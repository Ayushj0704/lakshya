@echo off
echo ============================================
echo   Lakshya Web Server
echo ============================================
echo.
echo Open http://localhost:8000 in your browser
echo Press Ctrl+C to stop the server.
echo.
cd /d "%~dp0"
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
