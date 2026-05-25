@echo off
echo ============================================
echo   MUNAI Digital Oilfield — Frontend Dev
echo ============================================
echo.
cd /d "%~dp0munai-digital-oilfield-ops-main"
echo Starting frontend on http://localhost:5173
echo Make sure backend is running on port 8000!
echo.
npm run dev
pause
