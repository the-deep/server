import datetime
from collections import defaultdict

import boto3
from django.conf import settings
from celery import shared_task

from deep.celery import app as celery_app, CeleryQueue


def _get_celery_queue_length_metric():
    queues_worker_count = defaultdict(list)
    queues_task_count = {}
    active_workers = []

    # Active workers
    ping_response = celery_app.control.inspect().ping()
    if ping_response is not None:
        for worker, resp in ping_response.items():
            if resp.get('ok') == 'pong':
                active_workers.append(worker)

    # Fetch queue task lengths
    for queue in CeleryQueue.ALL_QUEUES:
        queues_task_count[queue] = celery_app.backend.client.llen(queue)

    # Fetch queue worker lengths
    for worker, queues in celery_app.control.inspect().active_queues().items():
        if worker not in active_workers:
            continue
        for q in queues:
            queues_worker_count[q['name']].append(worker)

    current_timestamp = int(datetime.datetime.now().timestamp())
    for queue in CeleryQueue.ALL_QUEUES:
        task_count = queues_task_count.get(queue, 0)
        worker_count = len(queues_worker_count.get(queue, []))
        backlog_per_worker = task_count
        if worker_count != 0:
            backlog_per_worker = (task_count / worker_count)
        yield {
            'MetricName': 'celery-queue-backlog-per-worker',
            'Value': backlog_per_worker,
            'Unit': 'Percent',
            'Timestamp': current_timestamp,
            'Dimensions': [
                {
                    'Name': 'Environment',
                    'Value': settings.DEEP_ENVIRONMENT,
                },
                {
                    'Name': 'Queue',
                    'Value': queue,
                }
            ],
        }


@shared_task
def put_celery_query_metric():
    metrics = [
        *_get_celery_queue_length_metric(),
    ]

    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='DEEP',
        MetricData=metrics,
    )
