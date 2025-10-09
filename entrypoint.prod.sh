# #!/usr/bin/env bash

# python manage.py collectstatic --noinput
# python manage.py migrate --noinput
# gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 app.wsgi:application

#!/usr/bin/env bash

# Fix permissions for /app/staticfiles
echo "Fixing permissions..."
mkdir -p /app/staticfiles
chown -R appuser:appuser /app/staticfiles

# Run migrations and collect static files
echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 app.wsgi:application
