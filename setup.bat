@echo off
REM Setup script for AI Automation From Requirements (Windows)
REM This script creates a virtual environment and installs all dependencies

echo 🚀 Setting up AI Automation From Requirements...
echo.

REM Check Python version
python --version
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
    echo ✅ Virtual environment created!
) else (
    echo ℹ️  Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
echo 📥 Installing dependencies from requirements.txt...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✅ .env file created from .env.example
        echo ⚠️  Please edit .env file and add your GROQ_API_KEY
    ) else if exist "ENV_TEMPLATE.txt" (
        copy ENV_TEMPLATE.txt .env >nul
        echo ✅ .env file created from ENV_TEMPLATE.txt
        echo ⚠️  Please edit .env file and add your GROQ_API_KEY
    ) else (
        echo GROQ_API_KEY=your_api_key_here > .env
        echo ✅ .env file created with placeholder
        echo ⚠️  Please edit .env file and add your GROQ_API_KEY
    )
) else (
    echo ℹ️  .env file already exists
)

echo.
echo ✅ Setup complete!
echo.
echo To activate the virtual environment, run:
echo   .venv\Scripts\activate.bat
echo.
echo To run the application, run:
echo   streamlit run app.py
echo.
echo To deactivate the virtual environment, run:
echo   deactivate
echo.
pause
