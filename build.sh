#!/usr/bin/env bash
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install packages with --only-binary for Pillow and psycopg2-binary
# This forces pip to use pre-compiled wheels (no compilation)
pip install --only-binary :all: Pillow psycopg2-binary

# Install the rest normally
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate
