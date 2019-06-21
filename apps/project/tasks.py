from celery import shared_task

from utils.common import redis_lock
from entry.stats import get_project_entries_stats

from .models import Project


@shared_task
@redis_lock
def generate_entry_stats(project_id):
    project = Project.objects.get(pk=project_id)
    get_project_entries_stats(project)
