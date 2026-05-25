@echo off
echo ============================================
echo   MUNAI Digital Oilfield — Backend Server
echo ============================================
echo.
cd /d "%~dp0backend"
echo Starting FastAPI backend on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
