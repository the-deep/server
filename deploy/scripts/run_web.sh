#! /bin/bash

# /code/deploy/scripts/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$(dirname "$BASE_DIR")")

# echo '>> [Running] Django Collectstatic and Migrate'
# python3 $ROOT_DIR/manage.py collectstatic --no-input >> /var/log/deep.log 2>&1
# python3 $ROOT_DIR/manage.py migrate --no-input >> /var/log/deep.log 2>&1
uwsgi --ini $ROOT_DIR/deploy/configs/uwsgi.ini # Start uwsgi server
