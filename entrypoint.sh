#/bin/sh

python manage.py migrate --no-input
python manage.py collectstatic --no-input

gunicorn \
    -b '0.0.0.0:80' \
    -w $(( 2 * $(nproc) + 1 )) \
    phishstick.wsgi
