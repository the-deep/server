import logging
from datetime import timedelta

from celery import shared_task

from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def permanently_delete_users():
    # get all the user whose_deleted_at is null
    # and check if there deleted days greater than 30 days
    logger.info('[User Delete] Querying all the user with deleted_at')
    threshold = (
        timezone.now() - timedelta(days=settings.USER_AND_PROJECT_DELETE_IN_DAYS)
    )
    user_qs = User.objects.filter(
        profile__anonymized_at__isnull=True,
        profile__deleted_at__isnull=False,
        profile__deleted_at__lt=threshold,
    )
    logger.info(f'[User Delete] Found {user_qs.count()} users to delete.')
    for user in user_qs:
        logger.info(f'[User Delete] anonymizing user {user.id}')
        user.first_name = settings.DELETED_USER_FIRST_NAME
        user.last_name = settings.DELETED_USER_LAST_NAME
        user.email = user.username = f'user-{user.id}@deleted.thedeep.io'
        user.is_active = False
        # Profile
        profile = user.profile
        profile.invalid_email = True
        profile.organization = settings.DELETED_USER_ORGANIZATION
        profile.hid = None
        if profile.display_picture:
            profile.display_picture.delete()
        profile.anonymized_at = timezone.now()
        # Save
        user.save(update_fields=[
            'first_name',
            'last_name',
            'email',
            'username',
            'is_active',
        ])
        profile.save(update_fields=[
            'invalid_email',
            'organization',
            'hid',
            'display_picture',
            'anonymized_at',
        ])
        logger.info(f'[User Delete] Sucessfully anonymized user {user.id}')
