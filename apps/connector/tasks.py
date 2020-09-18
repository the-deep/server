import boto3
import json
import random
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from utils.common import redis_lock

from .serializers import SourceDataSerializer
from .models import (
    ConnectorLead,

    UnifiedConnector,
    UnifiedConnectorSource,
)

logger = logging.getLogger(__name__)


def invoke_lambda_function(lambda_function, body, lambda_client=None):
    lambda_client = lambda_client or boto3.client('lambda')
    response = json.load(
        lambda_client.invoke(
            FunctionName=lambda_function,
            InvocationType='RequestResponse',
            Payload=json.dumps({'body': body})
        )['Payload']
    )
    response_body = json.loads(response['body'])
    return response['statusCode'], response_body


class UnifiedConnectorTask():
    @staticmethod
    def invoke_source_extract_lambda_function(*args, **kwargs):
        return invoke_lambda_function(settings.DEEP_LAMBDA_SOURCE_EXTRACT, *args, **kwargs)

    @staticmethod
    def handle_source_extract_response(processed_leads):
        # All leads are already processed
        for processed_lead in processed_leads:
            connector_lead = ConnectorLead.objects.get(url=processed_lead['url'])
            connector_lead.status = (
                ConnectorLead.Status.SUCCESS if processed_lead['status'] == 'success'
                else ConnectorLead.Status.FAILURE
            )
            connector_lead.save()

    @classmethod
    def _process_unified_source(cls, source, project):
        # TODO: Clean all previous leads if params are changed
        params = source.params
        source_fetcher = source.source_fetcher()
        data, count = source_fetcher.get_leads(params)
        source_data = SourceDataSerializer(
            data,
            many=True,
            context={'project': project},
        ).data

        current_unified_source_leads_id = set(source.unifiedconnectorsourcelead_set.values_list('lead_id', flat=True))
        for lead_data in source_data:
            connector_lead, created = ConnectorLead.objects.get_or_create(
                url=lead_data['url'],
                defaults={'data': lead_data},
            )
            # if created or connector_lead.status is None:
            if created or connector_lead.status is None:
                # Connector lead which needs to be processed
                yield connector_lead.url
            if created or connector_lead.id not in current_unified_source_leads_id:
                # TODO: Add in bulk
                source.add_lead(connector_lead)

    @classmethod
    def _trigger_lambda_lead_extraction(cls, source, to_be_processed_urls):
        status_code, response_body = cls.invoke_source_extract_lambda_function({
            'sources': [{'url': url} for url in to_be_processed_urls],
            # ONLY FOR TESTING
            **({'source_key': source.source_id} if settings.TESTING else {}),
        })
        if status_code != 200:
            raise Exception(f'Failure from lambda response for {settings.DEEP_LAMBDA_SOURCE_EXTRACT}: {response_body}')

        lambda_existing_sources = response_body['existingSources']
        lambda_async_job_uuid = response_body['asyncJobUuid']

        if lambda_existing_sources:
            cls.handle_source_extract_response(lambda_existing_sources)

        if lambda_async_job_uuid:
            transaction.on_commit(
                lambda: pool_aws_lambda_source_extract.s(source.pk, lambda_async_job_uuid).apply_async(
                    countdown=random.uniform(20, 30),
                )
            )
            return True
        return False

    @classmethod
    @transaction.atomic  # @transaction.atomic is only used for transaction.on_commit
    def _process_unified_connector_source(cls, project, source):
        source.status = UnifiedConnectorSource.Status.PROCESSING
        source.save()
        try:
            to_be_processed_urls = list(cls._process_unified_source(source, project))
            if to_be_processed_urls:
                requires_pool = cls._trigger_lambda_lead_extraction(source, to_be_processed_urls)
                if not requires_pool:
                    source.status = UnifiedConnectorSource.Status.SUCCESS
            else:
                source.status = UnifiedConnectorSource.Status.SUCCESS
        except Exception:
            logger.error(f'Failed to process source: {source}', exc_info=True)
            source.status = UnifiedConnectorSource.Status.FAILURE
        source.last_calculated_at = timezone.now()
        source.generate_stats(commit=False)
        source.save()

    @classmethod
    def process_unified_connector(cls, unified_connector_id):
        unified_connector = UnifiedConnector.objects.get(pk=unified_connector_id)
        project = unified_connector.project

        if not unified_connector.is_active:
            logger.warning(f'Skippping processing for inactive connector {unified_connector.pk} {unified_connector}')
            return

        for source in unified_connector.unifiedconnectorsource_set.all():
            cls._process_unified_connector_source(project, source)


@shared_task
@redis_lock('process_unified_connector__{0}', timeout=60 * 15)
def process_unified_connector(unified_connector_id):
    UnifiedConnectorTask.process_unified_connector(unified_connector_id)


@shared_task(bind=True, max_retries=10)
def pool_aws_lambda_source_extract(self, source_id, lambda_async_job_uuid):
    retry_count = pool_aws_lambda_source_extract.request.retries
    source = UnifiedConnectorSource.objects.get(pk=source_id)
    status_code, response_body = UnifiedConnectorTask.invoke_source_extract_lambda_function({
        'asyncJobUuid': lambda_async_job_uuid,
        # ONLY FOR TESTING
        **({'retryCount': retry_count} if settings.TESTING else {}),
    })

    # body status are from deep-serverless
    if status_code != 200 or response_body['status'] in ['error', 'failed']:
        if status_code != 200:
            logger.error(f'Failed to invoke {settings.DEEP_LAMBDA_SOURCE_EXTRACT}: {response_body}')
        source.status = UnifiedConnectorSource.Status.FAILURE
    elif response_body['status'] == 'success':
        UnifiedConnectorTask.handle_source_extract_response(response_body['sources'])
        source.status = UnifiedConnectorSource.Status.SUCCESS
    else:
        source.status = UnifiedConnectorSource.Status.PROCESSING
        # Retry again 1 min
        self.retry(countdown=60 * retry_count)
    source.generate_stats(commit=False)
    source.save()
