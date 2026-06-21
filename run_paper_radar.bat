@echo off
setlocal

:: Change to the directory containing this .bat file
cd /d "%~dp0"

:: Activate virtualenv if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Run the bot
python -m paper_radar_bot.main
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: paper_radar_bot exited with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Done. Check the reports\ folder.
pause
