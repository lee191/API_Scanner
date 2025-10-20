@echo off
echo ========================================
echo Starting Test Application 3
echo Web Crawling Depth Test
echo Port: 5003
echo ========================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -q -r requirements.txt

REM Start the application
echo.
echo Starting server...
python app.py

pause
