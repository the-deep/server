import json
import logging
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.db import models
from redis_store import redis

from deep.models import ProcessStatus
from ary.stats import get_project_ary_entry_stats
from lead.models import Lead
from entry.models import Entry

from .models import (
    Project,
    ProjectStats,
    ProjectMembership,
)

logger = logging.getLogger(__name__)

VIZ_STATS_WAIT_LOCK_KEY = 'generate_project_viz_stats__wait_lock__{0}'
STATS_WAIT_LOCK_KEY = 'generate_project_stats__wait_lock'
STATS_WAIT_TIMEOUT = ProjectStats.THRESHOLD_SECONDS


def _generate_project_viz_stats(project_id):
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


def _generate_project_stats_cache():
    def _count_by_project_qs(qs):
        return {
            project: count
            for project, count in qs.order_by().values('project').annotate(
                count=models.Count('id', distinct=True)
            ).values_list('project', 'count')
        }

    def _count_by_project_date_qs(qs):
        data = defaultdict(list)
        for project, count, date in (
            qs
                .order_by('project', 'created_at__date')
                .values('project', 'created_at__date')
                .annotate(count=models.Count('id', distinct=True))
                .values_list('project', 'count', models.Func(models.F('created_at__date'), function='DATE'))
        ):
            data[project].append({
                'date': date and date.strftime('%Y-%m-%d'),
                'count': count,
            })
        return data

    current_time = timezone.now()
    threshold = current_time + relativedelta(months=-3)

    recent_leads = Lead.objects.filter(created_at__gte=threshold)
    recent_entries = Entry.objects.filter(created_at__gte=threshold)

    # Calculate
    leads_count_map = _count_by_project_qs(Lead.objects.all())
    leads_tagged_count_map = _count_by_project_qs(
        Lead.objects.annotate(
            entries_count=models.Subquery(
                Entry.objects.filter(
                    lead=models.OuterRef('pk'),
                ).order_by().values('lead').annotate(count=models.Count('id')).values('count')[:1],
                output_field=models.IntegerField()
            ),
        ).filter(entries_count__gt=0)
    )
    leads_tagged_and_verified_count_map = _count_by_project_qs(
        Lead.objects.annotate(
            entries_count=models.Subquery(
                Entry.objects.filter(
                    lead=models.OuterRef('pk'),
                ).order_by().values('lead').annotate(count=models.Count('id')).values('count')[:1],
                output_field=models.IntegerField()
            ),
            entries_verified_count=models.Subquery(
                Entry.objects.filter(
                    lead=models.OuterRef('pk'),
                    verified=True,
                ).order_by().values('lead').annotate(count=models.Count('id')).values('count')[:1],
                output_field=models.IntegerField()
            ),
        ).filter(entries_count__gt=0, entries_count=models.F('entries_verified_count'))
    )
    entries_count_map = _count_by_project_qs(Entry.objects.all())
    members_count_map = _count_by_project_qs(ProjectMembership.objects.all())

    # Recent lead/entry stats
    leads_activity_count_map = _count_by_project_qs(recent_leads)
    entries_activity_count_map = _count_by_project_qs(recent_entries)

    leads_activity_map = _count_by_project_date_qs(recent_leads)
    entries_activity_map = _count_by_project_date_qs(recent_entries)

    # Store
    for project in Project.objects.iterator():
        pk = project.pk
        project.stats_cache = dict(
            calculated_at=current_time.timestamp(),
            number_of_users=members_count_map.get(pk, 0),
            number_of_leads=leads_count_map.get(pk, 0),
            number_of_leads_tagged=leads_tagged_count_map.get(pk, 0),
            number_of_leads_tagged_and_verified=leads_tagged_and_verified_count_map.get(pk, 0),
            number_of_entries=entries_count_map.get(pk, 0),
            leads_activity=leads_activity_count_map.get(pk, 0),
            entries_activity=entries_activity_count_map.get(pk, 0),
            leads_activities=leads_activity_map.get(pk, []),
            entries_activities=entries_activity_map.get(pk, []),
        )
        project.save(update_fields=['stats_cache'])


@shared_task
def generate_viz_stats(project_id, force=False):
    """
    Generate stats data for Vizualization (Entry/Ary Viz)
    """
    key = VIZ_STATS_WAIT_LOCK_KEY.format(project_id)
    lock = redis.get_lock(key, STATS_WAIT_TIMEOUT)
    have_lock = lock.acquire(blocking=False)
    if not have_lock and not force:
        logger.warning(f'GENERATE_PROJECT_VIZ_STATS:: Waiting for timeout {key}')
        return False

    logger.info(f'GENERATE_PROJECT_STATS:: Processing for {key}')
    _generate_project_viz_stats(project_id)
    # NOTE: lock.release() is not called so that another process waits for timeout
    return True


@shared_task
def generate_project_stats_cache(force=False):
    """
    Generate stats data for Home
    """
    key = STATS_WAIT_LOCK_KEY
    lock = redis.get_lock(key, STATS_WAIT_TIMEOUT)
    have_lock = lock.acquire(blocking=False)
    if not have_lock and not force:
        logger.warning(f'GENERATE_PROJECT_STATS:: Waiting for timeout {key}')
        return False

    logger.info(f'GENERATE_PROJECT_STATS:: Processing for {key}')
    _generate_project_stats_cache()
    lock.release()
    return True
