@echo off
cd /d "%~dp0"
echo ===================================================
echo   AI Project Risk Advisor
echo ===================================================
echo Starting all microservices and frontend dashboard...
.\.venv\Scripts\python.exe scripts\run_all.py
pause
