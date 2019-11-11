import logging

from celery import shared_task
from django.core.management import call_command
from utils.common import redis_lock


logger = logging.getLogger(__name__)


@shared_task
@redis_lock('sync_organization_with_relief_web')
def sync_organization_with_relief_web():
    call_command('load_organizations')
    return True
