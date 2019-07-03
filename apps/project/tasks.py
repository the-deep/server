import json
import logging
import time

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from redis_store import redis
from deep.models import ProcessStatus
from utils.common import redis_lock
from entry.stats import get_project_entries_stats

from .models import Project, ProjectEntryStats

logger = logging.getLogger(__name__)

GES_WAIT_LOCK_KEY = 'generate_entry_stats__wait_lock__{0}'


@shared_task
@redis_lock('generate_entry_stats__{0}', 5 * 60)
def generate_entry_stats(project_id):
    ges_wait_lock_key = GES_WAIT_LOCK_KEY.format(project_id)
    if not redis.get_lock(ges_wait_lock_key, ProjectEntryStats.THRESHOLD_SECONDS).acquire(blocking=False):
        # logger.warning(f'GENERATE_ENTRY_STATS:: Waiting for timeout {ges_wait_lock_key}')
        return False

    time.sleep(10)
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
        project_entry_stats.status = ProcessStatus.FAILURE
        project_entry_stats.save()

    # Lock for another THRESHOLD_SECONDS
    redis.get_lock(GES_WAIT_LOCK_KEY.format(project_id), ProjectEntryStats.THRESHOLD_SECONDS).acquire(blocking=False)
