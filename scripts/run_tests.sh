#!/bin/bash -x

. /venv/bin/activate
if [ "$CI" == "true" ]; then
    pip install codecov

    set -e
    coverage run ./manage.py test -v 3
    coverage report
    coverage html
    codecov
    set +e
else
    ./manage.py test -v 3
fi
