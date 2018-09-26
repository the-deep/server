#!/bin/bash -x

. /venv/bin/activate
if [ "$CI" == "true" ]; then
    pip install codecov

    set -e
    coverage run --source jedi -m py.test
    coverage report
    coverage html
    codecov
    set +e
else
    py.test
fi
