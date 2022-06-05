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

from lead.filter_set import LeadGQFilterSet
from entry.filter_set import EntryGQFilterSet

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


def get_project_stats(project, info, filters):
    # XXX: Circular dependency
    from lead.schema import get_lead_qs
    from entry.schema import get_entry_qs

    def _count_by_project(qs):
        return qs\
            .filter(project=project)\
            .order_by().values('project')\
            .aggregate(count=models.Count('id', distinct=True))['count']

    if info.context.active_project:
        lead_qs = get_lead_qs(info)
        entry_qs = get_entry_qs(info)
    else:
        lead_qs = Lead.objects.filter(project=project)
        entry_qs = Entry.objects.filter(project=project, analysis_framework=project.analysis_framework_id)
    filters_counts = {}
    if filters:
        entry_filter_data = filters.get('entries_filter_data') or {}
        filtered_lead_qs = LeadGQFilterSet(request=info.context.request, queryset=lead_qs, data=filters).qs
        filtered_entry_qs = EntryGQFilterSet(
            request=info.context.request,
            queryset=entry_qs.filter(lead__in=filtered_lead_qs),
            data=entry_filter_data,
        ).qs
        filters_counts = dict(
            filtered_number_of_leads=_count_by_project(filtered_lead_qs),
            filtered_number_of_leads_not_tagged=_count_by_project(filtered_lead_qs.filter(status=Lead.Status.NOT_TAGGED)),
            filtered_number_of_leads_in_progress=_count_by_project(filtered_lead_qs.filter(status=Lead.Status.IN_PROGRESS)),
            filtered_number_of_leads_tagged=_count_by_project(filtered_lead_qs.filter(status=Lead.Status.TAGGED)),
            filtered_number_of_entries=_count_by_project(filtered_entry_qs),
            filtered_number_of_entries_verified=_count_by_project(filtered_entry_qs.filter(verified_by__isnull=False)),
            filtered_number_of_entries_controlled=_count_by_project(filtered_entry_qs.filter(controlled=True)),
        )
    counts = dict(
        number_of_users=_count_by_project(ProjectMembership.objects),
        number_of_leads=_count_by_project(lead_qs),
        number_of_leads_not_tagged=_count_by_project(lead_qs.filter(status=Lead.Status.NOT_TAGGED)),
        number_of_leads_in_progress=_count_by_project(lead_qs.filter(status=Lead.Status.IN_PROGRESS)),
        number_of_leads_tagged=_count_by_project(lead_qs.filter(status=Lead.Status.TAGGED)),
        number_of_entries=_count_by_project(entry_qs),
        number_of_entries_verified=_count_by_project(entry_qs.filter(verified_by__isnull=False)),
        number_of_entries_controlled=_count_by_project(entry_qs.filter(controlled=True)),
        **filters_counts,
    )
    for key, value in counts.items():
        setattr(project, key, value)
    return project


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

    geo_options = {}
    for region in region_qs:
        if region.geo_options is None:
            region.calc_cache()
        geo_options[region.pk] = region.geo_options

    project.geo_cache_file.save(
        f'project-geo-cache-{project.pk}.json',
        ContentFile(json.dumps(geo_options).encode('utf-8')),
        save=False,
    )
    project.geo_cache_hash = hash(tuple(region_qs.order_by('id').values_list('cache_index', flat=True)))
    project.save(update_fields=('geo_cache_hash', 'geo_cache_file'))
