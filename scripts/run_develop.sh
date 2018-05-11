#!/bin/bash -x

. /venv/bin/activate
pip3 install -r requirements.txt
python manage.py migrate --no-input
python manage.py createinitialrevisions
python manage.py runserver 0.0.0.0:8000 &
celery -A deep worker -l info
