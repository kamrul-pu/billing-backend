#!/usr/bin/env bash

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Starting server on port 8001..."
exec gunicorn --bind 0.0.0.0:8001 --workers 3 --threads 2 app.wsgi:application