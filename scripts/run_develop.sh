#!/bin/bash -x

pip3 install -r requirements.txt
python3 manage.py migrate --no-input
python3 manage.py createinitialrevisions
python3 manage.py runserver 0.0.0.0:8000 &
python3 manage.py run_celery_dev
