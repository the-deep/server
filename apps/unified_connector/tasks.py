import logging
from datetime import timedelta

from celery import shared_task
from deepl_integration.handlers import UnifiedConnectorLeadHandler
from django.db import models
from django.utils import timezone

from utils.common import redis_lock

from .models import ConnectorLead, ConnectorSource

logger = logging.getLogger(__name__)


@shared_task
@redis_lock("process_unified_connector_{0}", 60 * 60 * 0.5)
def process_unified_connector(_id):
    try:
        return UnifiedConnectorLeadHandler.process_unified_connector(_id)
    except Exception:
        logger.error("Unified connector process failed", exc_info=True)


@shared_task
@redis_lock("retry_connector_leads", 60 * 60 * 0.5)
def retry_connector_leads():
    try:
        return UnifiedConnectorLeadHandler.send_retry_trigger_request_to_extractor(ConnectorLead.objects.all())
    except Exception:
        logger.error("Retry connector lead failed", exc_info=True)


def trigger_connector_sources(max_execution_time, threshold, limit):
    sources_qs = (
        ConnectorSource.objects.annotate(
            execution_time=models.F("end_date") - models.F("start_date"),
        )
        .exclude(
            execution_time__isnull=False,
            status=ConnectorSource.Status.PROCESSING,
        )
        .filter(
            unified_connector__is_active=True,
            execution_time__lte=max_execution_time,
            last_fetched_at__lte=timezone.now() - threshold,
        )
        .order_by("execution_time")
    )

    processed_unified_connectors = set()
    for source in sources_qs.all()[:limit]:
        try:
            UnifiedConnectorLeadHandler.process_unified_connector_source(source)
            processed_unified_connectors.add(source.unified_connector_id)
        except Exception:
            logger.error("Failed to trigger connector source", exc_info=True)
    # Trigger connector leads
    for unified_connector_id in processed_unified_connectors:
        UnifiedConnectorLeadHandler.send_trigger_request_to_extractor(
            ConnectorLead.objects.filter(connectorsourcelead__source__unified_connector=unified_connector_id)
        )


@shared_task
@redis_lock("schedule_trigger_quick_unified_connectors", 60 * 60)
def schedule_trigger_quick_unified_connectors():
    # NOTE: Process connectors sources which have runtime <= 3 min and was processed 3 hours before.
    trigger_connector_sources(
        timedelta(minutes=3),
        timedelta(hours=3),
        20,
    )


@shared_task
@redis_lock("schedule_trigger_heavy_unified_connectors", 60 * 60)
def schedule_trigger_heavy_unified_connectors():
    # NOTE: Process connectors sources which have runtime <= 10 min and was processed 3 hours ago.
    trigger_connector_sources(
        timedelta(minutes=10),
        timedelta(hours=3),
        6,
    )


@shared_task
@redis_lock("schedule_trigger_super_heavy_unified_connectors", 60 * 60)
def schedule_trigger_super_heavy_unified_connectors():
    # NOTE: Process connectors sources which have runtime <= 1 hour and was processed 24 hours ago.
    trigger_connector_sources(
        timedelta(hours=1),
        timedelta(hours=24),
        10,
    )
