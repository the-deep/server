import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload


CMD = 'celery -A deep worker -B --concurrency=2 -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler'


def restart_celery(*args, **kwargs):
    kill_worker_cmd = 'pkill -9 celery'
    subprocess.call(shlex.split(kill_worker_cmd))
    subprocess.call(shlex.split(CMD))


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Starting celery worker with autoreload...')
        autoreload.main(restart_celery, args=None, kwargs=None)
