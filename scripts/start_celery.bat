@echo off
REM ═══════════════════════════════════════════════════════════════════
REM AI-Trading Celery Worker & Beat Startup
REM ═══════════════════════════════════════════════════════════════════

echo Starting AI-Trading Celery Services...
echo.

set DJANGO_SETTINGS_MODULE=crypto_platform.settings.local
set PYTHONPATH=%CD%

REM Start Celery Worker in new window
echo [1/2] Starting Celery Worker...
start "Celery Worker" cmd /k "cd /d %CD% && set DJANGO_SETTINGS_MODULE=crypto_platform.settings.local&& set PYTHONPATH=%CD%&& celery -A crypto_platform worker -l info --concurrency=4"

REM Wait 3 seconds
timeout /t 3 /nobreak > nul

REM Start Celery Beat in new window
echo [2/2] Starting Celery Beat...
start "Celery Beat" cmd /k "cd /d %CD% && set DJANGO_SETTINGS_MODULE=crypto_platform.settings.local&& set PYTHONPATH=%CD%&& celery -A crypto_platform beat -l info"

echo.
echo ═══════════════════════════════════════════════════════════════════
echo Celery services started!
echo   Worker:  Processing tasks in background
echo   Beat:    Scheduling recurring tasks
echo.
echo Scheduled Tasks:
echo   - News crawl:          Every 30 minutes
echo   - Signal generation:   Every hour
echo   - Signal evaluation:   Every hour
echo   - Weight adjustment:   Daily at 2:00 AM
echo   - BTC 6-hour cycle:    Every 6 hours
echo   - Weekly cycle:        Sundays at 2:00 AM
echo ═══════════════════════════════════════════════════════════════════
echo.
pause
