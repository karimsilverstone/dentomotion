@echo off
echo School Portal - Quick Start Script
echo ===================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Copy .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from .env.local...
    copy .env.local .env
)

REM Run migrations
echo Running migrations...
python manage.py migrate

REM Create superuser
echo.
set /p create_superuser="Do you want to create a superuser? (y/n): "
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ===================================
echo Setup complete!
echo To start the development server, run:
echo   python manage.py runserver
echo ===================================
pause

