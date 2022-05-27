import json
import logging
from collections import defaultdict

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.db import models
from redis_store import redis

from ary.stats import get_project_ary_entry_stats
from lead.models import Lead
from entry.models import Entry
from geo.models import GeoArea

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
    project_stats.status = ProjectStats.Status.STARTED
    project_stats.save()
    try:
        stats, stats_confidential = get_project_ary_entry_stats(project)
        project_stats.status = ProjectStats.Status.SUCCESS
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
        project_stats.status = ProjectStats.Status.FAILURE
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
    threshold = ProjectStats.get_activity_timeframe(current_time)

    # Make sure to only look for entries which have same AF as Project's AF
    all_entries_qs = Entry.objects.filter(analysis_framework=models.F('project__analysis_framework'))
    recent_leads = Lead.objects.filter(created_at__gte=threshold)
    recent_entries = all_entries_qs.filter(created_at__gte=threshold)

    # Calculate
    leads_count_map = _count_by_project_qs(Lead.objects.all())
    leads_tagged_and_controlled_count_map = _count_by_project_qs(
        Lead.objects.filter(status=Lead.Status.TAGGED).annotate(
            entries_count=models.Subquery(
                all_entries_qs.filter(
                    lead=models.OuterRef('pk'),
                ).order_by().values('lead').annotate(count=models.Count('id')).values('count')[:1],
                output_field=models.IntegerField()
            ),
            entries_controlled_count=models.Subquery(
                all_entries_qs.filter(
                    lead=models.OuterRef('pk'),
                    controlled=True,
                ).order_by().values('lead').annotate(count=models.Count('id')).values('count')[:1],
                output_field=models.IntegerField()
            ),
        ).filter(entries_count__gt=0, entries_count=models.F('entries_controlled_count'))
    )
    leads_not_tagged_count_map = _count_by_project_qs(Lead.objects.filter(status=Lead.Status.NOT_TAGGED))
    leads_in_progress_count_map = _count_by_project_qs(Lead.objects.filter(status=Lead.Status.IN_PROGRESS))
    leads_tagged_count_map = _count_by_project_qs(Lead.objects.filter(status=Lead.Status.TAGGED))

    entries_count_map = _count_by_project_qs(all_entries_qs)
    entries_verified_count_map = _count_by_project_qs(all_entries_qs.filter(verified_by__isnull=False))
    entries_controlled_count_map = _count_by_project_qs(all_entries_qs.filter(controlled=True))

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
            number_of_leads_tagged_and_controlled=leads_tagged_and_controlled_count_map.get(pk, 0),
            number_of_leads_not_tagged=leads_not_tagged_count_map.get(pk, 0),
            number_of_leads_in_progress=leads_in_progress_count_map.get(pk, 0),
            number_of_entries=entries_count_map.get(pk, 0),
            number_of_entries_verified=entries_verified_count_map.get(pk, 0),
            number_of_entries_controlled=entries_controlled_count_map.get(pk, 0),
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


def generate_project_geo_region_cache(project):
    region_qs = project.regions.defer('geo_options', 'centroid')
    geoarea_qs = GeoArea.objects.select_related('admin_level').order_by('admin_level__level')
    geo_options = {
        region.id: [
            {
                'label': '{} / {}'.format(
                    geo_area.admin_level.title,
                    geo_area.title,
                ),
                'title': geo_area.title,
                'key': str(geo_area.id),
                'admin_level': geo_area.admin_level.level,
                'admin_level_title': geo_area.admin_level.title,
                'region': region.id,
                'region_title': region.title,
                'parent': geo_area.parent.id if geo_area.parent else None,
            } for geo_area in geoarea_qs.filter(admin_level__region=region)
        ] for region in region_qs
    }
    project.geo_cache_file.save(
        f'project-geo-cache-{project.pk}.json',
        ContentFile(json.dumps(geo_options).encode('utf-8')),
        save=False,
    )
    project.geo_cache_hash = hash(tuple(region_qs.order_by('id').values_list('cache_index', flat=True)))
    project.save(update_fields=('geo_cache_hash', 'geo_cache_file'))
