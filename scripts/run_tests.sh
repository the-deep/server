#!/bin/bash -x

export PYTHONUNBUFFERED=1

if [ "$CI" == "true" ]; then
    pip3 install -r requirements.txt
    pip3 install codecov pytest-xdist
    python3 manage.py migrate --no-input
    python3 manage.py createinitialrevisions
    python3 manage.py run_celery_dev &

    set -e
    echo 'import coverage; coverage.process_startup()' > /code/sitecustomize.py
    COVERAGE_PROCESS_START=`pwd`/.coveragerc COVERAGE_FILE=`pwd`/.coverage PYTHONPATH=`pwd` py.test -n auto --dist=loadfile --durations=10
    coverage combine
    coverage report -i
    coverage html -i
    codecov
    set +e
else
    py.test
fi
