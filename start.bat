@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
)
echo.
echo   BJT DC Bias Web App
echo   Open http://127.0.0.1:5000 in your browser
echo   Press Ctrl+C to stop
echo.
start "" http://127.0.0.1:5000
.\.venv\Scripts\python run.py
pause
