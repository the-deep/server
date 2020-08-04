import json
import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from redis_store import redis
from deep.models import ProcessStatus
from ary.stats import get_project_ary_entry_stats

from .models import (
    Project,
    ProjectStats,
)

logger = logging.getLogger(__name__)

STATS_WAIT_LOCK_KEY = 'generate_project_stats__wait_lock__{0}'
STATS_WAIT_TIMEOUT = ProjectStats.THRESHOLD_SECONDS


def _generate_project_stats(project_id):
    project = Project.objects.get(pk=project_id)
    project_stats, _ = ProjectStats.objects.get_or_create(project=project)
    project_stats.status = ProcessStatus.STARTED
    project_stats.save()
    try:
        stats, stats_confidential = get_project_ary_entry_stats(project)
        project_stats.status = ProcessStatus.SUCCESS
        project_stats.modified_at = timezone.now()
        project_stats.file.save(
            f'project-stats-{project_id}.json',
            ContentFile(
                json.dumps(stats, cls=DjangoJSONEncoder).encode('utf-8'),
            ),
        )
        project_stats.confidential_file.save(
            f'project-stats-confidential-{project_id}.json',
            ContentFile(
                json.dumps(stats_confidential, cls=DjangoJSONEncoder).encode('utf-8'),
            ),
        )
        project_stats.save()
    except Exception:
        logger.warning(f'Ary Stats Generation Failed ({project_id})!!', exc_info=True)
        project_stats.status = ProcessStatus.FAILURE
        project_stats.save()


@shared_task
def generate_stats(project_id, force=False):
    key = STATS_WAIT_LOCK_KEY.format(project_id)
    lock = redis.get_lock(key, STATS_WAIT_TIMEOUT)
    have_lock = lock.acquire(blocking=False)
    if not have_lock and not force:
        logger.warning(f'GENERATE_PROJECT_STATS:: Waiting for timeout {key}')
        return False

    logger.info(f'GENERATE_PROJECT_STATS:: Processing for {key}')
    _generate_project_stats(project_id)
    # NOTE: lock.release() is not called so that another process waits for timeout
    return True
