#! /bin/bash

# /code/deploy/scripts/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$(dirname "$BASE_DIR")")


cd $ROOT_DIR
# Start celery
# SENTRY_DSN= celery flower -A deep --basic_auth=${FLOWER_BASIC_AUTHS} --address=0.0.0.0 --port=80 &

if ! [ -z "$CELERY_QUEUE" ]; then
    celery -A deep worker -B -l info \
        --statedb=celery-worker.state \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
    celery -A deep worker -B -l info \
        -Q $CELERY_QUEUE \
        --statedb=celery-worker.state \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler
fi
