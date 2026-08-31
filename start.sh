#!/bin/bash
set -e

# Run migrations
python manage.py migrate --no-input

# Collect static files (needed for production)
python manage.py collectstatic --no-input

# Use PORT if set, otherwise default to 8000
PORT=${PORT:-8000}

# Start Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
