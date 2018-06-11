import os
import fcntl
import boto3
import sys
import django
import botocore
import datetime
import requests

import logging

logger = logging.getLogger(__file__)

AWS_META_URL = 'http://169.254.169.254/latest/meta-data'

sys.path.append("/code/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deep.settings")
django.setup()

from deep.celery import app # noqae


def get_deployment_region():
    """
    Retrieve the instance deployment region
    """
    deployment_region_url = AWS_META_URL + "/placement/availability-zone"
    try:
        return requests.get(deployment_region_url).text[:-1]
    except requests.ConnectionError as err:
        print(err.message)
    pass


def get_ec2_instance_id():
    """Retrieve the instance id for the currently running EC2 instance. If
    the host machine is not an EC2 instance or is for some reason unable
    to make requests, return None.

    :returns: (str) id of the current EC2 instance
              (None) if the id could not be found"""

    instance_id_url = AWS_META_URL + "/instance-id"
    try:
        return requests.get(instance_id_url).text
    except requests.ConnectionError as err:
        print(err.message)


# FIXME: if get_deployment_region works 100%, remove this
os.environ['DEPLOYMENT_REGION'] = 'us-east-1'
# AWS CONFIGS
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_REGION_NAME = os.environ.get('DEPLOYMENT_REGION', get_deployment_region())
INSTANCE_ID = get_ec2_instance_id()

# METRIC CONFIG
METRIC_NAMESPACE = 'System/Linux'
METRIC_NAME = 'NumberOfCeleryWokers'
METRIC_UNIT = 'Count'


def get_autoscaling_group():
    """Retrieve the autoscaling group name of the current instance. If
    the host machine is not an EC2 instance, not subject to autoscaling,
    or unable to make requests, return None.

    :returns: (str) id of the current autoscaling group
              (None) if the autoscaling group could not be found"""

    try:
        autoscaling_client = boto3.client(
            "autoscaling",
            region_name=AWS_REGION_NAME,
        )
        return autoscaling_client.describe_auto_scaling_instances(
            InstanceIds=[INSTANCE_ID]
        )["AutoScalingInstances"][0]["AutoScalingGroupName"]
    except botocore.exceptions.BotoCoreError as err:
        print(err.message)
    except botocore.exceptions.ClientError as err:
        print(err.message)


def get_cloudwatch_client():
    """
    Return Cloudwatch Client
    """
    return boto3.client(
        'cloudwatch',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME,
    )


def put_metric():
    """
    Put Custom Metric to Cloudwatch
        * Number Of Celery workers
        * Metric Name is 'NumberOfCeleryWokers'
    """
    cloudwatch = get_cloudwatch_client()

    current_timestamp = int(datetime.datetime.now().timestamp())
    ping_response = app.control.inspect().ping()
    auto_scaling_group_name = get_autoscaling_group()
    number_of_workers = 0

    logger.info('Start: Ping Workers')

    for worker in ping_response:
        if(ping_response[worker].get('ok') == 'pong'):
            number_of_workers += 1

    metric_data = {
        'MetricName': METRIC_NAME,
        'Unit': METRIC_UNIT,
        'Value': number_of_workers,
        'Timestamp': current_timestamp,
        'Dimensions': [{
            'Name': 'AutoScalingGroupName',
            'Value': auto_scaling_group_name
        }],
    }

    logger.info('Sending: Number of Workers To Cloudwatch')
    logger.debug('Metric Data: %s', metric_data)

    cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=[metric_data],
    )
    logger.info('Finish Metric Push')


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    lock_filename = '/tmp/celery_worker_aws_metrics.lock'
    with open(lock_filename, 'w+') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise SystemExit('Alreay running')
        else:
            put_metric()
    os.remove(lock_filename)
