#!/bin/bash -x

export DOCKER_HOST_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

mkdir -p /var/run/celery/

python3 manage.py migrate --no-input
# python3 manage.py createinitialrevisions

if [ "${NO_CELERY}" == 'true' ]; then
    python3 manage.py runserver 0.0.0.0:8000
else
    python3 manage.py run_celery_dev &
    python3 manage.py runserver 0.0.0.0:8000
fi
