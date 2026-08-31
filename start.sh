#!/bin/bash
set -e

# Activate the virtual environment used by Nixpacks
source /opt/venv/bin/activate

# Create staticfiles directory if missing
mkdir -p staticfiles

# Migrate and collect static
python manage.py migrate --no-input
python manage.py collectstatic --no-input

# Use PORT from environment
PORT=${PORT:-8000}
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
