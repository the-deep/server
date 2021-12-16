#! /bin/bash

# /code/deploy/scripts/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$(dirname "$BASE_DIR")")


cd $ROOT_DIR
# Start celery
mkdir -p /var/run/celery/
# SENTRY_DSN= celery flower -A deep --basic_auth=${FLOWER_BASIC_AUTHS} --address=0.0.0.0 --port=80 &
celery -A deep worker -B --quiet -l info \
    --statedb=/var/run/celery/worker.state \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
