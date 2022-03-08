import copy
import logging
from typing import List

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils.encoding import DjangoUnicodeDecodeError

from utils.common import redis_lock, UidBase64Helper
from utils.request import RequestHelper
from deep.exceptions import DeepBaseException
from lead.tasks import LeadExtraction

from .token import connector_lead_extraction_token_generator
from .models import (
    ConnectorLead,
    ConnectorLeadPreviewImage,
    ConnectorSource,
    UnifiedConnector,
)


logger = logging.getLogger(__name__)


class UnifiedConnectorTask():
    class Exception():
        class InvalidTokenValue(DeepBaseException):
            default_message = 'Invalid Token'

        class InvalidOrExpiredToken(DeepBaseException):
            default_message = 'Invalid/expired token in client_id'

        class ConnectorLeadNotFound(DeepBaseException):
            default_message = 'No connector lead found for provided id'

    @staticmethod
    def get_callback_url():
        return (
            settings.DEEPL_SERVICE_CALLBACK_DOMAIN +
            reverse('connector_lead_extract_callback', kwargs={'version': 'v1'})
        )

    @staticmethod
    def generate_connector_lead_client_id(connector_lead: ConnectorLead) -> str:
        uid = UidBase64Helper.encode(connector_lead.pk)
        token = connector_lead_extraction_token_generator.make_token(connector_lead)
        return f'{uid}-{token}'

    @classmethod
    def get_connector_lead_from_client_id(cls, client_id):
        try:
            uidb64, token = client_id.split('-', 1)
            uid = UidBase64Helper.decode(uidb64)
        except (ValueError, DjangoUnicodeDecodeError):
            raise cls.Exception.InvalidTokenValue()
        if (connecor_lead := ConnectorLead.objects.filter(id=uid).first()) is None:
            raise cls.Exception.ConnectorLeadNotFound(f'No connector lead found for provided id: {uid}')
        if not connector_lead_extraction_token_generator.check_token(connecor_lead, token):
            raise cls.Exception.InvalidOrExpiredToken()
        return connecor_lead

    @staticmethod
    def save_connector_lead_data_from_extractor(
        connector_lead: ConnectorLead,
        extraction_success: bool,
        text_source_uri: str,
        images_uri: List[str],
        word_count: int,
        page_count: int,
    ):
        if not extraction_success:
            connector_lead.update_extraction_status(ConnectorLead.ExtractionStatus.FAILED)
            return connector_lead
        connector_lead.simplified_text = RequestHelper(url=text_source_uri, ignore_error=True).get_text() or ''
        connector_lead.word_count = word_count
        connector_lead.page_count = page_count
        for image in images_uri:
            lead_image = ConnectorLeadPreviewImage(connector_lead=connector_lead)
            image_obj = RequestHelper(url=image, ignore_error=True).get_file()
            if image_obj:
                lead_image.image.save(image_obj.name, image_obj)
                lead_image.save()
        connector_lead.update_extraction_status(ConnectorLead.ExtractionStatus.SUCCESS, commit=False)
        connector_lead.save()
        return connector_lead

    @classmethod
    def _process_unified_source(cls, source):
        params = copy.deepcopy(source.params)
        source_fetcher = source.source_fetcher()
        leads, _ = source_fetcher.get_leads(params)

        current_source_leads_id = set(source.source_leads.values_list('connector_lead_id', flat=True))
        for connector_lead in leads:
            connector_lead, _ = ConnectorLead.get_or_create_from_lead(connector_lead)
            if connector_lead.id not in current_source_leads_id:
                source.add_lead(connector_lead)

    @classmethod
    def send_retry_trigger_request_to_extractor(
        cls, connector_leads_qs: models.QuerySet[ConnectorLead],
        chunk_size=500,
    ) -> int:
        connector_leads = list(  # Fetch all now
            connector_leads_qs
            .filter(extraction_status=ConnectorLead.ExtractionStatus.RETRYING)
            .only('id', 'url').distinct()[:chunk_size]
        )
        extraction_status = ConnectorLead.ExtractionStatus.RETRYING
        if LeadExtraction.send_trigger_request_to_extractor(
            [
                {
                    'url': connector_lead.url,
                    'client_id': UnifiedConnectorTask.generate_connector_lead_client_id(connector_lead),
                }
                for connector_lead in connector_leads
            ],
            cls.get_callback_url(),
        ):  # True if request is successfully send
            extraction_status = ConnectorLead.ExtractionStatus.STARTED
        return ConnectorLead.objects\
            .filter(pk__in=[c.pk for c in connector_leads])\
            .update(extraction_status=extraction_status)

    @classmethod
    def _send_trigger_request_to_extractor(cls, connector_leads_qs: models.QuerySet[ConnectorLead]):
        paginator = Paginator(
            connector_leads_qs.filter(extraction_status=ConnectorLead.ExtractionStatus.PENDING).only('id', 'url').distinct(),
            100,
        )
        while True:
            page = paginator.page(1)
            connector_leads: List[ConnectorLead] = list(page.object_list)
            if not connector_leads:  # Nothing to process anymore
                break
            extraction_status = ConnectorLead.ExtractionStatus.RETRYING
            if LeadExtraction.send_trigger_request_to_extractor(
                [
                    {
                        'url': connector_lead.url,
                        'client_id': UnifiedConnectorTask.generate_connector_lead_client_id(connector_lead),
                    }
                    for connector_lead in connector_leads
                ],
                cls.get_callback_url(),
            ):  # True if request is successfully send
                extraction_status = ConnectorLead.ExtractionStatus.STARTED
            ConnectorLead.objects\
                .filter(pk__in=[c.pk for c in connector_leads])\
                .update(extraction_status=extraction_status)

    @classmethod
    def _process_unified_connector_source(cls, source):
        source.status = ConnectorSource.Status.PROCESSING
        source.save(update_fields=('status',))
        source.last_fetched_at = timezone.now()
        try:
            # Fetch leads
            cls._process_unified_source(source)
            source.status = ConnectorSource.Status.SUCCESS
            source.generate_stats(commit=False)
            source.save(update_fields=('status', 'stats', 'last_fetched_at',))
        except Exception:
            source.status = ConnectorSource.Status.FAILURE
            logger.error(f'Failed to process source: {source}', exc_info=True)
            source.save(update_fields=('status', 'last_fetched_at',))

    @classmethod
    def process_unified_connector(cls, unified_connector_id):
        unified_connector = UnifiedConnector.objects.get(pk=unified_connector_id)
        if not unified_connector.is_active:
            logger.warning(f'Skippping processing for inactive connector (pk:{unified_connector.pk}) {unified_connector}')
            return
        for source in unified_connector.sources.all():
            cls._process_unified_connector_source(source)
        # Send trigger to extractor
        cls._send_trigger_request_to_extractor(
            ConnectorLead.objects.filter(connectorsourcelead__source__unified_connector=unified_connector)
        )


@shared_task
@redis_lock('process_unified_connector_{0}', 60 * 60 * 0.5)
def process_unified_connector(_id):
    try:
        return UnifiedConnectorTask.process_unified_connector(_id)
    except Exception:
        logger.error('Unified connector process failed', exc_info=True)


@shared_task
@redis_lock('retry_connector_leads', 60 * 60 * 0.5)
def retry_connector_leads():
    try:
        return UnifiedConnectorTask.send_retry_trigger_request_to_extractor(
            ConnectorLead.objects.all()
        )
    except Exception:
        logger.error('Retry connector lead failed', exc_info=True)
