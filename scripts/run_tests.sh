#!/bin/bash -x

export PYTHONUNBUFFERED=1
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$CI" == "true" ]; then
    pip3 install coverage pytest-xdist

    set -e
    # Wait until database is ready
    $BASE_DIR/wait-for-it.sh ${DATABASE_HOST:-db}:${DATABASE_PORT-5432}

    # To show migration logs
    ./manage.py test -v 2 deep.tests.test_fake

    # Run all tests now
    echo 'import coverage; coverage.process_startup()' > /code/sitecustomize.py
    COVERAGE_PROCESS_START=`pwd`/.coveragerc COVERAGE_FILE=`pwd`/.coverage PYTHONPATH=`pwd` py.test -n auto --reuse-db --dist=loadfile --durations=10

    # Collect/Generate reports
    coverage combine
    coverage report -i
    coverage html -i
    coverage xml
    set +e
else
    py.test
fi
