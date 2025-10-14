# Create fresh file
cat > entrypoint.prod.sh << 'EOF'
#!/usr/bin/env bash

python manage.py migrate --noinput
gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 app.wsgi:application
EOF

# Make it executable
chmod +x entrypoint.prod.sh