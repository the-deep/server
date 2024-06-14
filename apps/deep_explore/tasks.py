import datetime
import logging
import time
from typing import Tuple, Union

import pytz
from analysis_framework.models import Widget
from celery import shared_task
from commons.schema_snapshots import SnapshotQuery, generate_query_snapshot
from dateutil.relativedelta import relativedelta
from django.db import connection, models, transaction
from django.test import override_settings
from django.utils import timezone
from djangorestframework_camel_case.util import underscoreize
from entry.models import Attribute, Entry
from export.tasks.tasks_projects import generate_projects_stats
from geo.models import GeoArea
from project.models import Project

from utils.common import redis_lock

from .models import (
    AggregateTracker,
    EntriesCountByGeoAreaAggregate,
    PublicExploreSnapshot,
)

logger = logging.getLogger(__name__)


class DateHelper:
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
            WITH entry_geo_data as (
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
            SELECT * FROM entry_geo_data WHERE EXISTS (
                SELECT 1 from {_tb(GeoArea)}
                WHERE id = entry_geo_data.geo_area_id
                LIMIT 1
            )
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
        from_date = Entry.objects.aggregate(date=models.Min("created_at__date"))["date"]
    until_date = timezone.now().date()  # NOTE: Stats will not include this date

    params = dict(
        from_date=DateHelper.str(from_date),
        until_date=DateHelper.str(until_date),
    )
    if from_date is None or from_date >= until_date:
        logger.info(f"Nothing to do here...{params}")
        return

    with transaction.atomic():
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute(get_update_entries_count_by_geo_area_aggregate_sql(), params)
            logger.info(f"Rows affected: {cursor.rowcount}")
        logger.info(f"Successfull. Runtime: {time.time() - start_time} seconds")
        tracker.value = until_date
        logger.info(f"Saving date {tracker.value} as last tracker")
        tracker.save()


def generate_public_deep_explore_snapshot():
    def get_or_create(_type: PublicExploreSnapshot.Type, start_date: datetime.date, end_date: datetime.date, **kwargs):
        snapshot = PublicExploreSnapshot.objects.get_or_create(
            type=_type,
            **kwargs,
            defaults=dict(
                start_date=start_date,
                end_date=end_date,
            ),
        )[0]
        # For already existing
        snapshot.start_date = start_date
        snapshot.end_date = end_date
        return snapshot

    def _get_date_filter(min_date: datetime.date, max_date: datetime.date) -> dict:
        return {
            "dateFrom": min_date.isoformat(),
            "dateTo": max_date.isoformat(),
        }

    def _get_date_meta(min_year, max_year) -> Tuple[Tuple[datetime.date, datetime.date], dict]:
        min_date = datetime.datetime(year=min_year, month=1, day=1, tzinfo=pytz.UTC)
        max_date = datetime.datetime(year=max_year, month=1, day=1, tzinfo=pytz.UTC) - relativedelta(days=1)
        return (
            min_date.date(),
            max_date.date(),
        ), _get_date_filter(min_date, max_date)

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "unique-snowflake",
            }
        },
    )
    def _save_snapshot(
        gql_query,
        filters,
        snapshot_filename,
        snapshot,
        generate_download_file=True,
    ):
        file_content, errors = generate_query_snapshot(gql_query, {"filter": filters})
        if file_content is None:
            logger.error(f"Failed to generate: {errors}", exc_info=True)
            return
        # Delete current file
        snapshot.file.delete()
        # Save new file
        snapshot.file.save(f"{snapshot_filename}.json", file_content)
        if generate_download_file:  # Skip for Global snapshots
            # Generate
            download_file = generate_projects_stats(
                # CamelCase to snake_case
                underscoreize(filters),
                None,
            )
            # Delete current file
            snapshot.download_file.delete()
            # Save new file
            snapshot.download_file.save(f"{snapshot_filename}.csv", download_file)
        snapshot.save()

    # Global year range
    data_min_date = Project.objects.aggregate(min_created_at=models.Min("created_at"))["min_created_at"]
    data_max_date = timezone.now() - relativedelta(days=1)
    date_range, date_filter = (data_min_date, data_max_date), _get_date_filter(data_min_date, data_max_date)
    # Global - Time series
    _save_snapshot(
        SnapshotQuery.DeepExplore.GLOBAL_TIME_SERIES,
        date_filter,
        "Global-time-series-snapshot",
        get_or_create(
            PublicExploreSnapshot.Type.GLOBAL,
            *date_range,
            global_type=PublicExploreSnapshot.GlobalType.TIME_SERIES,
        ),
        generate_download_file=False,
    )
    # Global - Full
    _save_snapshot(
        SnapshotQuery.DeepExplore.GLOBAL_FULL,
        date_filter,
        "Global-full-snapshot",
        get_or_create(
            PublicExploreSnapshot.Type.GLOBAL,
            *date_range,
            global_type=PublicExploreSnapshot.GlobalType.FULL,
        ),
    )
    # By year
    for year in range(data_min_date.year, data_max_date.year + 1):
        date_range, date_filter = _get_date_meta(year, year + 1)
        _save_snapshot(
            SnapshotQuery.DeepExplore.YEARLY,
            date_filter,
            f"{year}-snapshot",
            get_or_create(
                PublicExploreSnapshot.Type.YEARLY_SNAPSHOT,
                *date_range,
                year=year,
            ),
        )


@shared_task
@redis_lock("update_deep_explore_entries_count_by_geo_aggreagate")
def update_deep_explore_entries_count_by_geo_aggreagate_task():
    # Weekly clean-up old data and calculate from start.
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.weekday
    start_over = False
    if timezone.now().weekday() == 6:  # Every sunday
        start_over = True
    return update_deep_explore_entries_count_by_geo_aggreagate(start_over=start_over)


@shared_task
@redis_lock("update_public_deep_explore_snapshot")
def update_public_deep_explore_snapshot():
    return generate_public_deep_explore_snapshot()
