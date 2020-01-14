#!/bin/bash -x

export PYTHONUNBUFFERED=1

if [ "$CI" == "true" ]; then
    pip3 install -r requirements.txt
    pip3 install codecov pytest-xdist
    python3 manage.py migrate --no-input
    python3 manage.py createinitialrevisions
    python3 manage.py run_celery_dev &

    set -e
    coverage run -m py.test -n 3
    coverage report -i
    coverage html -i
    codecov
    set +e
else
    py.test
fi
