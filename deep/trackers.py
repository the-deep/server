from enum import Enum, auto, unique
from typing import Type

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone
from project.models import Project
from user.models import Profile

from deep.caches import CacheKey


class TrackerAction:
    @unique
    class Project(Enum):
        READ = auto()
        WRITE = auto()


def track_project(project: Project, action: TrackerAction.Project = TrackerAction.Project.READ):
    cache_key = CacheKey.Tracker.LAST_PROJECT_READ_ACCESS_DATETIME
    if action == TrackerAction.Project.WRITE:
        cache_key = CacheKey.Tracker.LAST_PROJECT_WRITE_ACCESS_DATETIME
    cache.set(
        cache_key + str(project.pk),
        timezone.now(),
        None,  # Cache value forever until manually removed
    )


def track_user(user_profile: Profile):
    cache.set(
        CacheKey.Tracker.LAST_USER_ACTIVE_DATETIME + str(user_profile.pk),
        timezone.now(),
        None,  # Cache value forever until manually removed
    )


@transaction.atomic
def update_entity_data_in_bulk(
    Model: Type[models.Model],
    cache_key_prefix: str,
    field: str,
):
    cache_keys = cache.keys(cache_key_prefix + "*")
    entities_update = []
    for key, value in cache.get_many(cache_keys).items():
        entities_update.append(
            Model(
                **{
                    "id": key.split(cache_key_prefix)[1],
                    field: value,
                }
            )
        )
    if entities_update:
        Model.objects.bulk_update(entities_update, fields=[field], batch_size=200)
    transaction.on_commit(lambda: cache.delete_many(cache_keys))


def update_project_data_in_bulk():
    # -- Read
    update_entity_data_in_bulk(
        Project,
        CacheKey.Tracker.LAST_PROJECT_READ_ACCESS_DATETIME,
        "last_read_access",
    )
    # -- Write
    update_entity_data_in_bulk(
        Project,
        CacheKey.Tracker.LAST_PROJECT_WRITE_ACCESS_DATETIME,
        "last_write_access",
    )
    # -- Update project->status using last_write_access
    # -- -- To active
    Project.objects.filter(
        last_write_access__lte=timezone.now() - relativedelta(months=Project.PROJECT_INACTIVE_AFTER_MONTHS),
        status=Project.Status.ACTIVE,
    ).update(
        status=Project.Status.INACTIVE,
    )
    # -- -- To inactive
    Project.objects.filter(
        last_write_access__isnull=False,
    ).exclude(
        last_write_access__lte=timezone.now() - relativedelta(months=Project.PROJECT_INACTIVE_AFTER_MONTHS),
        status=Project.Status.INACTIVE,
    ).update(
        status=Project.Status.ACTIVE,
    )


def update_user_data_in_bulk():
    update_entity_data_in_bulk(
        Profile,
        CacheKey.Tracker.LAST_USER_ACTIVE_DATETIME,
        "last_active",
    )
    # -- Update user->profile-is_active using last_active
    # -- -- To active
    Profile.objects.filter(
        last_active__lte=timezone.now() - relativedelta(months=Profile.USER_INACTIVE_AFTER_MONTHS),
        is_active=True,
    ).update(
        is_active=False,
    )
    # -- -- To inactive
    Profile.objects.filter(
        last_active__isnull=False,
    ).exclude(
        last_active__lte=timezone.now() - relativedelta(months=Profile.USER_INACTIVE_AFTER_MONTHS),
        is_active=False,
    ).update(
        is_active=True,
    )


@shared_task
def schedule_tracker_data_handler():
    """
    Read tracker data from cache and update respective DB data
    """
    update_project_data_in_bulk()
    update_user_data_in_bulk()
