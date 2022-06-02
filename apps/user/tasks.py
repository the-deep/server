import logging

from celery import shared_task

from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@shared_task
def user_deletion(force=False):
    # get all the user whose_deleted_at is null
    # and check if there deleted days greater than 30 days
    logger.info('Querying all the user with deleted_at')
    user_qs = User.objects.filter(
        profile__deleted_at__isnull=False
    )
    today = timezone.now().date()
    for user in user_qs:
        if abs((user.profile.deleted_at - today).days) > 30:  # HardCode this here?
            logger.info(f'Deleting User {user.id}')
            user.delete()
