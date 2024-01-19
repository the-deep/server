import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from utils.common import redis_lock
from deepl_integration.handlers import LeadExtractionHandler

from .models import Lead

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=10)
@redis_lock('lead_extraction_{0}', 60 * 60 * 0.5)
def extract_from_lead(self, lead_id):
    """
    A task to auto extract text and images from a lead.

    * Lead should have a valid attachment or url.
    * It needs to be checked whether this task from the same lead is already going on.
    """
    try:
        lead = Lead.objects.get(pk=lead_id)
        if lead.extraction_status == Lead.ExtractionStatus.SUCCESS:
            return
        return LeadExtractionHandler.trigger_lead_extract(lead, task_instance=self)
    except Exception:
        logger.error('Lead Core Extraction Failed!!', exc_info=True)


@shared_task
def generate_previews(lead_ids=None):
    """Generate previews of leads which do not have preview"""
    lead_ids = lead_ids or Lead.objects.filter(
        Q(leadpreview__isnull=True) |
        Q(leadpreview__text_extract=''),
    ).values_list('id', flat=True)

    for lead_id in lead_ids:
        extract_from_lead.apply_async((lead_id,), countdown=1)


@shared_task
@redis_lock('remaining_lead_extract', 60 * 60 * 0.5)
def remaining_lead_extract():
    """
    This task looks for pending, failed, retrying leads which are dangling.
    Then triggers their extraction.
    """
    THRESHOLD_DAYS = 1
    PROCCESS_LEADS_PER_STATUS = 50

    threshold = timezone.now() - timedelta(days=-THRESHOLD_DAYS)
    for status in [
        Lead.ExtractionStatus.PENDING,
        Lead.ExtractionStatus.STARTED,
        Lead.ExtractionStatus.RETRYING,
    ]:
        queryset = Lead.objects.filter(
            extraction_status=status,
            modified_at__lt=threshold,
        )
        count = queryset.count()
        if count == 0:
            continue
        logger.info(f'[Lead Extraction] {status.label}: {count}')
        for lead_id in queryset.values_list('id', flat=True)[:PROCCESS_LEADS_PER_STATUS]:
            extract_from_lead(lead_id)
