@echo off
REM Quick start script for Windows
echo ========================================
echo AI Agent Vietnamese Translator
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import langchain_google_genai" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create .env file and add your GEMINI_API_KEY
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

REM Run setup
echo Running setup...
python setup.py

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To run translation:
echo   python main.py
echo.
echo To run tests:
echo   pytest tests/ -v
echo.
pause
