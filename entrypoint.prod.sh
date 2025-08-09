python app/manage.py collectstatic --noinput
python app/manage.py migrate --noinput
python -m --bind 0.0.0.0:8000 --workers 3 gunicorn app.wsgi:application