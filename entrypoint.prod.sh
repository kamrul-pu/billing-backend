# #!/usr/bin/env bash

# python manage.py collectstatic --noinput
# python manage.py migrate --noinput
# gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 app.wsgi:application

#!/bin/bash

# Ensure staticfiles dir is writable
echo "Fixing permissions for /app/staticfiles..."
chown -R appuser:appuser /app/staticfiles

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 3
