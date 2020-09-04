import logging
from celery import shared_task
from django.utils import timezone

from .serializer import SourceDataSerializer
from .models import (
    ConnectorLead,

    UnifiedConnector,
    UnifiedConnectorSource,
)

logger = logging.getLogger(__name__)


def _process_unified_source(unified_source, project):
    params = unified_source.params
    source_fetcher = unified_source.source_fetcher()
    data, count = source_fetcher.get_leads(params)
    source_data = SourceDataSerializer(
        data,
        many=True,
        context={'project': project},
    ).data

    unified_source_leads_id = set(unified_source.unifiedconnectorsourcelead_set.values_list('lead_id', flat=True))
    for lead_data in source_data:
        connector_lead, created = ConnectorLead.objects.get_or_create(
            url=lead_data['url'],
            defaults={'data': lead_data},
        )
        if created or connector_lead.status is None:
            yield connector_lead.url
        if created or connector_lead.id not in unified_source_leads_id:
            # TODO: Add in bulk
            unified_source.add_lead(connector_lead)


def _process_unified_connector(unified_connector_id):
    unified_connector = UnifiedConnector.objects.get(pk=unified_connector_id)
    new_leads_url = []

    for unified_source in unified_connector.unifiedconnectorsource_set.all():
        project = unified_connector.project
        try:
            new_leads_url.extend(_process_unified_source(unified_source, project))
        except Exception:
            logger.error(f'Failed to process source: {unified_source}', exc_info=True)
            unified_source.status = UnifiedConnectorSource.Status.FAILURE

        unified_source.last_calculated_at = timezone.now()
        unified_source.status = UnifiedConnectorSource.Status.PROCESSING
        unified_source.save()

    new_leads_url = [lead.id for lead in new_leads]


@shared_task
def process_unified_connector(unified_connector_id):
    _process_unified_connector(unified_connector_id)
