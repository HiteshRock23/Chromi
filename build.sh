#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating media directories..."
mkdir -p media/uploads
mkdir -p media/converted

echo "Fixing Pillow ANTIALIAS compatibility..."
python fix_pillow_antialias.py

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Build completed successfully!" 