import logging
import datetime
import time
import json
from typing import Union
from celery import shared_task

from django.db import connection, models, transaction
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.base import ContentFile
from django.utils import timezone
from django.test import override_settings
from djangorestframework_camel_case.util import underscoreize

from deep.schema import schema as gql_schema
from utils.common import redis_lock
from entry.models import Entry, Attribute
from project.models import Project
from analysis_framework.models import Widget
from export.tasks.tasks_projects import generate_projects_stats

from .models import (
    AggregateTracker,
    EntriesCountByGeoAreaAggregate,
    PublicExploreYearSnapshot,
)

logger = logging.getLogger(__name__)


class DateHelper():
    @staticmethod
    def py_date(string: Union[str, None]) -> Union[datetime.date, None]:
        if string:
            return datetime.datetime.strptime(string, "%Y-%m-%d").date()

    @staticmethod
    def str(date: Union[datetime.date, None]) -> Union[str, None]:
        if date:
            return date.strftime("%Y-%m-%d")


def _tb(model):
    # Return database table name
    return model._meta.db_table


DEEP_EXPLORE_WITH_FILTER_QUERY = """
    query MyQuery($filter: ExploreDeepFilterInputType!) {
      deepExploreStats(filter: $filter) {
        totalActiveUsers
        totalAuthors
        totalEntries
        totalEntriesAddedLastWeek
        totalLeads
        totalProjects
        totalPublishers
        totalRegisteredUsers
        topTenPublishers {
          id
          title
          leadsCount
          projectsCount
        }
        topTenProjectsByUsers {
          id
          title
          usersCount
        }
        topTenProjectsByEntries {
          id
          title
          entriesCount
          leadsCount
        }
        topTenProjectsByLeads {
          id
          title
          entriesCount
          leadsCount
        }
        topTenFrameworks {
          id
          title
          projectsCount
          entriesCount
        }
        topTenAuthors {
          id
          title
          projectsCount
          leadsCount
        }
        projectsByRegion {
          id
          centroid
          projectIds
        }
      }
    }
"""

DEEP_EXPLORE_FULL_QUERY = """
    query MyQuery($filter: ExploreDeepFilterInputType!) {
      deepExploreStats(filter: $filter) {
        projectsCountByMonth {
          count
          date
        }
        projectsCountByDay {
          count
          date
        }
        leadsCountByMonth {
          date
          count
        }
        leadsCountByDay {
          date
          count
        }
        entriesCountByRegion {
          centroid
          count
        }
        entriesCountByMonth {
          date
          count
        }
        entriesCountByDay {
          date
          count
        }
      }
    }
"""


def get_update_entries_count_by_geo_area_aggregate_sql():
    """
    geo_attributes_qs = Attribute.objects\
        .filter(widget__widget_id=Widget.WidgetType.GEO)
    qs = geo_attributes_qs.filter(
        entry__created_at__gte=from_date,
        entry__created_at__lt=until_date,
    ).annotate(
        geo_area=models.Func(
            models.F('data__value'),
            function='jsonb_array_elements_text',
        ),
        date=TruncDay('entry__created_at'),
        project=models.F('entry__project'),
    ).order_by('date', 'project').values('date', 'project', 'geo_area').annotate(
        entries_count=models.Count('id', distinct=True),
    ).values('date', 'project', 'geo_area', 'entries_count')
    """
    # NOTE: Above Django Queryset is used to generate below SELECT SQL Query
    return f"""
        INSERT INTO "{_tb(EntriesCountByGeoAreaAggregate)}" (
            project_id,
            geo_area_id,
            date,
            entries_count
        )
        (
            SELECT
              "{_tb(Entry)}".project_id AS project_id,
              JSONB_ARRAY_ELEMENTS_TEXT(
                  ("{_tb(Attribute)}".data->'value')
              )::int AS geo_area_id,
              DATE_TRUNC(
                  'day',
                  "{_tb(Entry)}".created_at AT TIME ZONE 'UTC'
              ) AS date,
              COUNT(DISTINCT "{_tb(Attribute)}".id) AS entries_count
            FROM
              "{_tb(Attribute)}"
              INNER JOIN "{_tb(Widget)}" ON ("{_tb(Attribute)}".widget_id = "{_tb(Widget)}".id)
              INNER JOIN "{_tb(Entry)}" ON ("{_tb(Attribute)}".entry_id = "{_tb(Entry)}".id)
            WHERE
                "{_tb(Widget)}".widget_id = 'geoWidget'
                AND "{_tb(Entry)}".created_at >= %(from_date)s
                AND "{_tb(Entry)}".created_at < %(until_date)s
            GROUP BY
              JSONB_ARRAY_ELEMENTS_TEXT(
                  ("{_tb(Attribute)}".data->'value')
              ),
              DATE_TRUNC(
                  'day',
                  "{_tb(Entry)}".created_at AT TIME ZONE 'UTC'
              ),
              "{_tb(Entry)}".project_id
            ORDER BY date, project_id
        )
        ON CONFLICT (project_id, geo_area_id, date)
        DO UPDATE SET
            entries_count = EXCLUDED.entries_count;
    """


def update_deep_explore_entries_count_by_geo_aggreagate(start_over=False):
    tracker = AggregateTracker.latest(AggregateTracker.Type.ENTRIES_COUNT_BY_GEO_AREA)
    if start_over:
        # Clean all previous data
        tracker.value = None
        # Truncate table and sequences
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {_tb(EntriesCountByGeoAreaAggregate)} RESTART IDENTITY;")
            tracker.save()
        logger.warning("Removed all previous data.")

    if tracker.value:
        # Use tracker data if available
        from_date = DateHelper.py_date(tracker.value)
    else:
        # Look at entry data
        from_date = Entry.objects.aggregate(date=models.Min('created_at__date'))['date']
    until_date = timezone.now().date()  # NOTE: Stats will not include this date

    params = dict(
        from_date=DateHelper.str(from_date),
        until_date=DateHelper.str(until_date),
    )
    if from_date is None or from_date >= until_date:
        logger.info(f'Nothing to do here...{params}')
        return

    with transaction.atomic():
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute(get_update_entries_count_by_geo_area_aggregate_sql(), params)
            logger.info(f'Rows affected: {cursor.rowcount}')
        logger.info(f"Successfull. Runtime: {time.time() - start_time} seconds")
        tracker.value = until_date
        logger.info(f"Saving date {tracker.value} as last tracker")
        tracker.save()


def generate_public_deep_explore_snapshot():
    class DummyContext:
        request = None

    class DummyExport:
        exported_by = None
        filters = None

    def _get_date_filter(min_year, max_year):
        return {
            'dateFrom': f"{min_year}-01-01T00:00:00Z",
            'dateTo': f"{max_year}-01-01T00:00:00Z",
        }

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        },
    )
    def _save_snapshot(
        gql_query,
        filters,
        year,
        snapshot_filename
    ):
        result = gql_schema.execute(
            gql_query,
            context=DummyContext(),
            variables={
                'filter': filters,
            }
        )
        if result.errors:
            logger.error(f'Failed to generate: {result.errors}', exc_info=True)
            return
        snapshot = PublicExploreYearSnapshot.objects.filter(year=year).first() or PublicExploreYearSnapshot(year=year)
        file_content = ContentFile(json.dumps(result.data, cls=DjangoJSONEncoder).encode('utf-8'))
        # Delete current file
        snapshot.file.delete()
        # Save new file
        snapshot.file.save(f'{snapshot_filename}.json', file_content)
        if year != 0:  # Skip for Global snapshots
            # Generate
            download_file = generate_projects_stats(
                # CamelCase to snake_case
                underscoreize(filters),
                None,
            )
            # Delete current file
            snapshot.download_file.delete()
            # Save new file
            snapshot.download_file.save(f'{snapshot_filename}.csv', download_file)
        snapshot.save()

    data_min_year = Project.objects.aggregate(min_year=models.Min('created_at__year'))['min_year']
    data_max_year = timezone.now().year
    # Global
    _save_snapshot(
        DEEP_EXPLORE_FULL_QUERY,
        _get_date_filter(data_min_year, data_max_year),
        0,
        'Global-snapshot'
    )
    # By year
    for year in range(data_min_year, data_max_year + 1):
        _save_snapshot(
            DEEP_EXPLORE_WITH_FILTER_QUERY,
            _get_date_filter(year, year + 1),
            year,
            f'{year}-snapshot',
        )


@shared_task
@redis_lock('update_deep_explore_entries_count_by_geo_aggreagate')
def update_deep_explore_entries_count_by_geo_aggreagate_task():
    # Weekly clean-up old data and calculate from start.
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.weekday
    start_over = False
    if timezone.now().weekday() == 6:  # Every sunday
        start_over = True
    return update_deep_explore_entries_count_by_geo_aggreagate(start_over=start_over)


@shared_task
@redis_lock('update_public_deep_explore_snapshot')
def update_public_deep_explore_snapshot():
    return generate_public_deep_explore_snapshot()
