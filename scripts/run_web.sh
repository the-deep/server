#!/bin/bash -x

export DOCKER_HOST_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

# python3 manage.py migrate --no-input
# python3 manage.py createinitialrevisions

python3 manage.py runserver 0.0.0.0:8000
