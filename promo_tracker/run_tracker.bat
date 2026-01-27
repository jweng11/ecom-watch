@echo off
REM Laptop Promotion Tracker - Windows Launcher
REM Double-click this file to run the tracker

echo ============================================================
echo   LAPTOP PROMOTION TRACKER
echo ============================================================
echo.

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY is not set.
    echo.
    echo To set it permanently:
    echo   1. Press Windows + R
    echo   2. Type: rundll32 sysdm.cpl,EditEnvironmentVariables
    echo   3. Add ANTHROPIC_API_KEY with your API key
    echo.
    echo Or set it temporarily for this session:
    echo   set ANTHROPIC_API_KEY=your-key-here
    echo.
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Run the tracker
python tracker.py

echo.
echo ============================================================
echo   COMPLETE - Check your Documents\laptop_promo_tracker folder
echo ============================================================
echo.
pause
