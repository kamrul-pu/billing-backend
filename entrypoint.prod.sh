#!/usr/bin/env bash
set -e

echo "Starting Django application..."

# Wait for database to be ready (only if using PostgreSQL)
if [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Waiting for database..."
    python manage.py wait_for_db
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --worker-class gthread \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app.wsgi:application