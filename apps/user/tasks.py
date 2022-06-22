import logging
from datetime import datetime, timedelta

from celery import shared_task

from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def user_deletion(force=False):
    # get all the user whose_deleted_at is null
    # and check if there deleted days greater than 30 days
    logger.info('Querying all the user with deleted_at')
    today = timezone.now().date()
    user_qs = User.objects.filter(
        profile__deleted_at__isnull=False,
        profile__deleted_at__lte=datetime.now() - timedelta(days=30)
    )
    today = timezone.now().date()
    for user in user_qs:
        if abs((user.profile.deleted_at - today).days) > settings.USER_AND_PROJECT_DELETE_IN_DAYS:
            logger.info(f'Updating user {user.username}')
            user.first_name = settings.DELETED_USER_FIRST_NAME
            user.last_name = settings.DELETED_USER_LAST_NAME
            user.email = f'user-{user.id}@deleted.thedeep.io'
            user.username = f'user-{user.id}@deleted.thedeep.io'
            user.profile.invalid_email = True
            user.is_active = False
            user.profile.organization = settings.DELETED_USER_ORGANIZATION
            user.save(update_fields=['first_name', 'last_name', 'email', 'username', 'is_active'])
            logger.info(f'Sucessfully Updated user {user.id}')
