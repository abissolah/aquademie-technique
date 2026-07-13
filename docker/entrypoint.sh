#!/bin/bash
set -e

python manage.py wait_for_db --timeout "${DB_WAIT_TIMEOUT:-60}"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${DJANGO_DEBUG}" = "True" ] || [ "${DJANGO_DEBUG}" = "true" ]; then
    exec python manage.py runserver 0.0.0.0:8000
fi

exec gunicorn club_plongee.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
