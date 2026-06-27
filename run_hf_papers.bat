@echo off
setlocal

:: Change to the directory containing this .bat file
cd /d "%~dp0"

:: Activate virtualenv if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Run HuggingFace trending papers report
set PYTHONPATH=%~dp0src
python -m paper_radar_bot.hf_main
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: hf_main exited with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Done. Check the reports\ folder for prbHF热门论文_*.html
pause
