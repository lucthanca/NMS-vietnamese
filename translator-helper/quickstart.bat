@echo off
REM Quick start script for NMS MXML Translator Helper
REM This script sets up the environment and runs the application

echo ====================================
echo NMS MXML Translator Helper
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Run the application
echo Starting application...
echo.
python run.py

REM Deactivate virtual environment
deactivate
