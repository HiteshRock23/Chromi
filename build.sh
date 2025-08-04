#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create media directories if they don't exist
mkdir -p media/uploads
mkdir -p media/converted

python manage.py collectstatic --no-input
python manage.py migrate 