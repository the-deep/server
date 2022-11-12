import shlex
import os
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload
from deep.celery import CeleryQueue


WORKER_STATE_DIR = '/var/run/celery'

CMD = (
    f"celery -A deep worker -Q {','.join(CeleryQueue.ALL_QUEUES)} -B --concurrency=2 -l info "
    '--scheduler django_celery_beat.schedulers:DatabaseScheduler '
    f'--statedb={WORKER_STATE_DIR}/worker.state'
)


def restart_celery(*args, **kwargs):
    kill_worker_cmd = 'pkill -9 celery'
    subprocess.call(shlex.split(kill_worker_cmd))
    subprocess.call(shlex.split(CMD))


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Starting celery worker with autoreload...')
        if not os.path.exists(WORKER_STATE_DIR):
            os.makedirs(WORKER_STATE_DIR)
        autoreload.run_with_reloader(restart_celery, args=None, kwargs=None)
