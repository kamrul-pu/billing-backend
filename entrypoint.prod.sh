#!/usr/bin/env bash

# Wait for database to be ready
python manage.py wait_for_db

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the application
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 app.wsgi:application