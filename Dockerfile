FROM python:3.12-slim

# Install system dependencies (required for psycopg2 and other packages)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files – now works because we fixed the import
RUN python manage.py collectstatic --no-input

# Expose port 3000 (adjust if needed)
EXPOSE 3000

# Start the server with gunicorn (or your chosen command)
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "config.wsgi:application"]
