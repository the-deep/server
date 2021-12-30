#! /bin/bash

# /code/deploy/scripts/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$(dirname "$BASE_DIR")")


cd $ROOT_DIR
# Start celery
# SENTRY_DSN= celery flower -A deep --basic_auth=${FLOWER_BASIC_AUTHS} --address=0.0.0.0 --port=80 &

celery_args=

# Add queue if provided
if ! [ -z "$CELERY_QUEUE" ]; then
    celery_args="$celery_args-Q $CELERY_QUEUE "
fi

# Set max tasks per child count if provided
if ! [ -z "$CELERY_MAX_TASKS_PER_CHILD" ]; then
    celery_args="$celery_args--max-tasks-per-child  $CELERY_MAX_TASKS_PER_CHILD "
fi

if [[ $CELERY_RUN_BEAT == "true"  ]]; then
    celery_args="$celery_args--statedb=celery-worker.state --scheduler django_celery_beat.schedulers:DatabaseScheduler "
fi

celery -A deep worker -B -l info $celery_args
