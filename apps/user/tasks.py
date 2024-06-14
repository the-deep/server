import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def permanently_delete_users():
    # get all the user whose_deleted_at is null
    # and check if there deleted days greater than 30 days
    logger.info("[User Delete] Querying all the user with deleted_at")
    threshold = timezone.now() - timedelta(days=settings.USER_AND_PROJECT_DELETE_IN_DAYS)
    user_qs = User.objects.filter(
        profile__original_data__isnull=False,
        profile__deleted_at__isnull=False,
        profile__deleted_at__lt=threshold,
    )
    logger.info(f"[User Delete] Found {user_qs.count()} users to delete.")
    for user in user_qs:
        logger.info(f"[User Delete] Cleaning up user original data {user.id}")
        user.profile.original_data = None
        user.profile.save(update_fields=("original_data",))
        logger.info(f"[User Delete] Successfully deleted all user data from the system {user.id}")
