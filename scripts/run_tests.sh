#!/bin/bash -x

if [ "$CI" == "true" ]; then
    pip3 install codecov

    set -e
    coverage run -m py.test
    coverage report
    coverage html
    codecov
    set +e
else
    py.test
fi
