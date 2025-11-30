#!/bin/bash

echo "School Portal - Quick Start Script"
echo "==================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.local..."
    cp .env.local .env
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser
echo ""
echo "Do you want to create a superuser? (y/n)"
read create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "==================================="
echo "Setup complete!"
echo "To start the development server, run:"
echo "  python manage.py runserver"
echo "==================================="

