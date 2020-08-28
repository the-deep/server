#! /bin/bash

# /code/deploy/scripts/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# /code/
ROOT_DIR=$(dirname "$(dirname "$BASE_DIR")")
instid=`curl -s -o - http://169.254.169.254/latest/meta-data/instance-id`

export EBS_HOSTNAME=${DEPLOYMENT_ENV_NAME}_${instid}
crontab $ROOT_DIR/deploy/cronjobs

### ENV FOR CRON JOBS
printenv | sed 's/^\([a-zA-Z0-9_]*\)=\(.*\)$/export \1="\2"/g' > /aws-script/env_var.sh
cron

### PAPERTRAIL CONFIGS
cp $ROOT_DIR/deploy/configs/log_files.yml-sample /etc/log_files.yml
sed "s/hostname:.*/hostname: $EBS_HOSTNAME/" -i /etc/log_files.yml
sed "s/host:.*/host: $PAPERTRAIL_HOST/" -i /etc/log_files.yml
sed "s/port:.*/port: $PAPERTRAIL_PORT/" -i /etc/log_files.yml
service remote_syslog start # start remote_syslog for papaertail log collecter
###

echo 'System Info:'
echo 'HOSTNAME:     ' ${EBS_HOSTNAME}
echo 'EBS_ENV_TYPE: ' ${EBS_ENV_TYPE}
echo 'WORKER_TYPE:  ' ${WORKER_TYPE}
echo 'Allowed Host: ' ${DJANGO_ALLOWED_HOST}
echo '######################################'

# To start workers [Channels/Celery]
if [ "$EBS_ENV_TYPE" == "worker" ]; then
    echo 'Worker Environment'
    cd $ROOT_DIR

    if [ "$WORKER_TYPE" == "celery" ]; then
        echo '>> Starting Celery Worker'
        # Start celery
        mkdir -p /var/log/celery/
        SENTRY_DSN= celery flower -A deep --basic_auth=${FLOWER_BASIC_AUTHS} --address=0.0.0.0 --port=80 &
        celery -A deep worker -B --quiet -l info \
            --logfile=/var/log/celery/celery.log \
            --scheduler django_celery_beat.schedulers:DatabaseScheduler
    elif [ "$WORKER_TYPE" == "channel" ]; then
        echo '>> Starting Django Channels'
        # Start channels
        mkdir -p /var/log/daphne/
        daphne -b 0.0.0.0 -p 80 --access-log /var/log/daphne/access.log deep.asgi:channel_layer \
            >> /var/log/daphne/access.log 2>&1 &
        python3 manage.py runworker >> /var/log/daphne/access.log 2>&1
    fi

fi

# To start Django Server [API]
if [ "$EBS_ENV_TYPE" == "web" ]; then

    echo 'API Environment'
    if [ -z "$NO_DJANGO_MIGRATION" ]; then
        echo '>> [Running] Django Collectstatic and Migrate'
        python3 $ROOT_DIR/manage.py collectstatic --no-input >> /var/log/deep.log 2>&1
        python3 $ROOT_DIR/manage.py migrate --no-input >> /var/log/deep.log 2>&1
    else # Variable Set
        # NOTE: Running migrate and collectstatic from elasticbeanstalk post deploy (For ElasticBeanstalk)
        echo '>> [Not Running] Django Collectstatic and Migrate, because ENV: NO_DJANGO_MIGRATION is set'
    fi
    uwsgi --ini $ROOT_DIR/deploy/configs/uwsgi.ini # Start uwsgi server
fi
