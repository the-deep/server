import json
import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from redis_store import redis
from deep.models import ProcessStatus
from entry.stats import get_project_entries_stats

from .models import Project, ProjectEntryStats

logger = logging.getLogger(__name__)

STATS_WAIT_LOCK_KEY = 'generate_entry_stats__wait_lock__{0}'
STATS_WAIT_TIMEOUT = ProjectEntryStats.THRESHOLD_SECONDS


def _generate_entry_stats(project_id):
    project = Project.objects.get(pk=project_id)
    project_entry_stats, _ = ProjectEntryStats.objects.get_or_create(project=project)
    project_entry_stats.status = ProcessStatus.STARTED
    project_entry_stats.save()
    try:
        entry_stats = get_project_entries_stats(project)
        project_entry_stats.status = ProcessStatus.SUCCESS
        project_entry_stats.modified_at = timezone.now()
        project_entry_stats.file.save(
            f'project-stats-{project_id}.json',
            ContentFile(
                json.dumps(entry_stats, cls=DjangoJSONEncoder).encode('utf-8'),
            ),
        )
        project_entry_stats.save()
    except Exception:
        logger.warning(f'Entry Stats Generation Failed ({project_id})!!', exc_info=True)
        project_entry_stats.status = ProcessStatus.FAILURE
        project_entry_stats.save()


@shared_task
def generate_entry_stats(project_id, force=False):
    key = STATS_WAIT_LOCK_KEY.format(project_id)
    lock = redis.get_lock(key, STATS_WAIT_TIMEOUT)
    have_lock = lock.acquire(blocking=False)
    if not have_lock and not force:
        logger.warning(f'GENERATE_ENTRY_STATS:: Waiting for timeout {key}')
        return False

    logger.info(f'GENERATE_ENTRY_STATS:: Processing for {key}')
    _generate_entry_stats(project_id)
    # NOTE: lock.release() is not called so that another process waits for timeout
    return True
