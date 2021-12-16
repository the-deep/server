#!/bin/bash -x

export DOCKER_HOST_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

mkdir -p /var/run/celery/

python3 manage.py run_celery_dev
