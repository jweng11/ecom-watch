@echo off
REM Laptop Promotion Tracker - Windows Setup Script
REM Run this once to install dependencies

echo ============================================================
echo   LAPTOP PROMOTION TRACKER - SETUP
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python from python.org
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Installing Playwright browser...
playwright install chromium
if errorlevel 1 (
    echo ERROR: Failed to install Playwright browser
    pause
    exit /b 1
)

echo.
echo [3/3] Creating output folder...
if not exist "%USERPROFILE%\Documents\laptop_promo_tracker" (
    mkdir "%USERPROFILE%\Documents\laptop_promo_tracker"
    mkdir "%USERPROFILE%\Documents\laptop_promo_tracker\screenshots"
)

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo   1. Set your API key (see below)
echo   2. Double-click run_tracker.bat to run
echo.
echo To set ANTHROPIC_API_KEY:
echo   - Press Windows + R
echo   - Type: rundll32 sysdm.cpl,EditEnvironmentVariables
echo   - Click "New" under User variables
echo   - Name: ANTHROPIC_API_KEY
echo   - Value: your-api-key-here
echo.
pause
