FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies for PostgreSQL and Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Collect static files at build time
RUN python manage.py collectstatic --no-input

# Expose the port your app listens on
EXPOSE 3000

# Run migrations, collect static (again, to catch any new files), then start Gunicorn
CMD ["sh", "-c", "python manage.py migrate --no-input && python manage.py collectstatic --no-input && gunicorn config.wsgi:application --bind 0.0.0.0:3000"]
