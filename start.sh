#!/bin/bash
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input

# Use PORT from environment, fallback to 8000
PORT=${PORT:-8000}
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
