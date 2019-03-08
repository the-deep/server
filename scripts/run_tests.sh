#!/bin/bash -x

export PYTHONUNBUFFERED=1

if [ "$CI" == "true" ]; then
    pip3 install -r requirements.txt
    pip3 install codecov
    python3 manage.py migrate --no-input
    python3 manage.py createinitialrevisions
    python3 manage.py run_celery_dev &

    set -e
    coverage run -m py.test
    coverage report
    coverage html
    codecov
    set +e
else
    py.test
fi
