#!/bin/bash -x

export PYTHONUNBUFFERED=1
PYTHON_MYPY_DEP_PATH=/code/.mypy-dep/

pip3 install -r requirements.txt

if [ "${USING_MYPY}" == 'true' ]; then
    # TODO: better/faster way?
    rm -rf $PYTHON_MYPY_DEP_PATH/*
    pip3 install -r requirements.txt -t $PYTHON_MYPY_DEP_PATH
    rm -rf $PYTHON_MYPY_DEP_PATH/typing_extensions*
fi

python3 manage.py migrate --no-input
# python3 manage.py createinitialrevisions

if [ "${NO_CELERY}" == 'true' ]; then
    python3 manage.py runserver 0.0.0.0:8000
else
    python3 manage.py run_celery_dev &
    python3 manage.py runserver 0.0.0.0:8000
fi
