@echo off
REM Creates a Windows Task Scheduler task to run tracker weekly
REM Run this as Administrator

echo ============================================================
echo   SCHEDULING WEEKLY TRACKER RUN
echo ============================================================
echo.

REM Get the current directory
set SCRIPT_DIR=%~dp0

REM Create the scheduled task
schtasks /create /tn "LaptopPromoTracker" /tr "cmd /c cd /d \"%SCRIPT_DIR%\" && python tracker.py" /sc weekly /d SUN /st 09:00 /f

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Try running this script as Administrator.
    echo.
    echo Manual setup:
    echo   1. Open Task Scheduler (search "Task Scheduler" in Start)
    echo   2. Click "Create Basic Task"
    echo   3. Name: LaptopPromoTracker
    echo   4. Trigger: Weekly, Sunday at 9:00 AM
    echo   5. Action: Start a program
    echo      - Program: cmd
    echo      - Arguments: /c cd /d "%SCRIPT_DIR%" ^&^& python tracker.py
    echo.
) else (
    echo.
    echo SUCCESS! Task "LaptopPromoTracker" created.
    echo It will run every Sunday at 9:00 AM.
    echo.
    echo To view/modify: Open Task Scheduler and look for "LaptopPromoTracker"
    echo To delete: schtasks /delete /tn "LaptopPromoTracker" /f
    echo.
)

pause
