#!/bin/sh
set -eu

# On Azure, uploads live in /home/data/media; copy in the photos bundled with
# the code without overwriting anything already uploaded on the live site.
if [ -d /home/site/wwwroot ] && [ -z "${MEDIA_ROOT:-}" ] && [ -d media ]; then
    mkdir -p /home/data/media
    cp -Rn media/. /home/data/media/ 2>/dev/null || true
fi

python manage.py migrate --noinput

# Creates the admin account from DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD
# app settings if it doesn't exist yet, so a fresh database always has a login.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    python manage.py createsuperuser --noinput >/dev/null 2>&1 || true
fi
python manage.py regenerate_qr_codes
python manage.py collectstatic --noinput

exec gunicorn burgerbills.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -