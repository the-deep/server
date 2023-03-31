import os
import json
import copy
import requests
import logging
from typing import List, Type
from functools import reduce
from urllib.parse import urlparse

from django.conf import settings
from django.urls import reverse
from django.utils.encoding import DjangoUnicodeDecodeError
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction, models

from deep.token import DeepTokenGenerator
from deep.deepl import DeeplServiceEndpoint
from utils.common import UidBase64Helper, get_full_media_url
from utils.request import RequestHelper
from deep.exceptions import DeepBaseException

from assisted_tagging.models import (
    DraftEntry,
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
    AssistedTaggingPrediction,
)
from unified_connector.models import (
    ConnectorLead,
    ConnectorLeadPreviewImage,
    ConnectorSource,
    UnifiedConnector,
)
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)
from lead.typings import NlpExtractorUrl

logger = logging.getLogger(__name__)


class DefaultClientIdGenerator(DeepTokenGenerator):
    key_salt = "deepl-integration-callback-client-id"

    def _make_hash_value(self, instance, timestamp):
        return str(type(instance)) + str(instance.pk) + str(timestamp)


class BaseHandler:
    REQUEST_HEADERS = {'Content-Type': 'application/json'}

    # --- Override
    # Optional
    client_id_generator = DefaultClientIdGenerator()

    # Required
    model: Type[models.Model]
    callback_url_name: str

    class Exception:
        class InvalidTokenValue(DeepBaseException):
            default_message = 'Invalid Token'

        class InvalidOrExpiredToken(DeepBaseException):
            default_message = 'Invalid/expired token in client_id'

        class ObjectNotFound(DeepBaseException):
            default_message = 'No draft entry found for provided id'

    @classmethod
    def get_callback_url(cls, **kwargs):
        return (
            settings.DEEPL_SERVICE_CALLBACK_DOMAIN +
            reverse(
                cls.callback_url_name, kwargs={
                    'version': 'v1',
                    **kwargs,
                },
            )
        )

    @classmethod
    def get_client_id(cls, instance: models.Model) -> str:
        uid = UidBase64Helper.encode(instance.pk)
        token = cls.client_id_generator.make_token(instance)
        return f'{uid}-{token}'

    @classmethod
    def get_object_using_client_id(cls, client_id):
        """
        Parse client id and return related object
        - Raise error if invalid/404/expired
        """
        try:
            uidb64, token = client_id.split('-', 1)
            uid = UidBase64Helper.decode(uidb64)
        except (ValueError, DjangoUnicodeDecodeError):
            raise cls.Exception.InvalidTokenValue()
        if (instance := cls.model.objects.filter(id=uid).first()) is None:
            raise cls.Exception.ObjectNotFound(f'No {cls.model.__name__} found for provided id: {uid}')
        if not cls.client_id_generator.check_token(instance, token):
            raise cls.Exception.InvalidOrExpiredToken()
        return instance

    @classmethod
    def send_trigger_request_to_extractor(cls, *_):
        raise Exception('Not implemented yet.')

    @classmethod
    def save_data(cls, *_):
        raise Exception('Not implemented yet.')


class AssistedTaggingDraftEntryHandler(BaseHandler):
    model = DraftEntry
    callback_url_name = 'assisted_tagging_draft_entry_prediction_callback'

    @classmethod
    def send_trigger_request_to_extractor(cls, draft_entry):
        source_organization = draft_entry.lead.source
        author_organizations = [
            author.data.title
            for author in draft_entry.lead.authors.all()
        ]
        payload = {
            'entries': [
                {
                    'client_id': cls.get_client_id(draft_entry),
                    'entry': draft_entry.excerpt,
                }
            ],
            'lead': draft_entry.lead_id,
            'project': draft_entry.project_id,
            'publishing_organization': source_organization and source_organization.data.title,
            'authoring_organization': author_organizations,
            'callback_url': cls.get_callback_url(),
        }
        try:
            response = requests.post(
                DeeplServiceEndpoint.ASSISTED_TAGGING_ENTRY_PREDICT_ENDPOINT,
                headers=cls.REQUEST_HEADERS,
                json=payload
            )
            if response.status_code == 200:
                return True
        except Exception:
            logger.error('Assisted tagging send failed, Exception occurred!!', exc_info=True)
            draft_entry.prediction_status = DraftEntry.PredictionStatus.SEND_FAILED
            draft_entry.save(update_fields=('prediction_status',))
        _response = locals().get('response')
        logger.error(
            'Assisted tagging send failed!!',
            extra={
                'payload': payload,
                'response': _response.content if _response else None
            },
        )

    # --- Callback logics
    @staticmethod
    def _get_or_create_models_version(models_data):
        def get_versions_map():
            return {
                (model_version.model.model_id, model_version.version): model_version
                for model_version in AssistedTaggingModelVersion.objects.filter(
                    reduce(
                        lambda acc, item: acc | item,
                        [
                            models.Q(
                                model__model_id=model_data['id'],
                                version=model_data['version'],
                            )
                            for model_data in models_data
                        ],
                    )
                ).select_related('model').all()
            }

        existing_model_versions = get_versions_map()
        new_model_versions = [
            model_data
            for model_data in models_data
            if (model_data['id'], model_data['version']) not in existing_model_versions
        ]

        if new_model_versions:
            AssistedTaggingModelVersion.objects.bulk_create([
                AssistedTaggingModelVersion(
                    model=AssistedTaggingModel.objects.get_or_create(
                        model_id=model_data['id'],
                        defaults=dict(
                            name=model_data['id'],
                        ),
                    )[0],
                    version=model_data['version'],
                )
                for model_data in models_data
            ])
            existing_model_versions = get_versions_map()
        return existing_model_versions

    @classmethod
    def _get_or_create_tags_map(cls, tags):
        from assisted_tagging.tasks import sync_tags_with_deepl_task

        def get_tags_map():
            return {
                tag_id: _id
                for _id, tag_id in AssistedTaggingModelPredictionTag.objects.values_list('id', 'tag_id')
            }

        current_tags_map = get_tags_map()
        # Check if new tags needs to be created
        new_tags = [
            tag for tag in tags
            if tag not in current_tags_map
        ]
        if new_tags:
            # Create new tags
            AssistedTaggingModelPredictionTag.objects.bulk_create([
                AssistedTaggingModelPredictionTag(
                    name=new_tag,
                    tag_id=new_tag,
                )
                for new_tag in new_tags
            ])
            # Refetch
            current_tags_map = get_tags_map()
            sync_tags_with_deepl_task.delay()
        return current_tags_map

    @classmethod
    def _process_model_preds(cls, model_version, current_tags_map, draft_entry, model_prediction):
        prediction_status = model_prediction['prediction_status']
        draft_entry.prediction_status = DraftEntry.PredictionStatus.DONE
        if prediction_status == 0:  # If 0 no tags are provided
            return

        tags = model_prediction.get('tags', {})  # NLP TagId
        values = model_prediction.get('values', [])  # Raw value

        common_attrs = dict(
            model_version=model_version,
            draft_entry_id=draft_entry.id,
        )
        new_predictions = []
        for category_tag, tags in tags.items():
            for tag, prediction_data in tags.items():
                prediction_value = prediction_data.get('prediction')
                threshold_value = prediction_data.get('prediction')
                is_selected = prediction_data.get('is_selected', False)
                new_predictions.append(
                    AssistedTaggingPrediction(
                        **common_attrs,
                        data_type=AssistedTaggingPrediction.DataType.TAG,
                        category_id=current_tags_map[category_tag],
                        tag_id=current_tags_map[tag],
                        prediction=prediction_value,
                        threshold=threshold_value,
                        is_selected=is_selected,
                    )
                )

        for value in set(values):
            new_predictions.append(
                AssistedTaggingPrediction(
                    **common_attrs,
                    data_type=AssistedTaggingPrediction.DataType.RAW,
                    value=value,
                    is_selected=True,
                )
            )
        AssistedTaggingPrediction.objects.bulk_create(new_predictions)

    @classmethod
    def save_data(cls, draft_entry, data):
        model_preds = data['model_preds']
        # Save if new tags are provided
        current_tags_map = cls._get_or_create_tags_map([
            tag
            for prediction in model_preds
            for category_tag, tags in prediction.get('tags', {}).items()
            for tag in [
                category_tag,
                *tags.keys(),
            ]
        ])
        models_version_map = cls._get_or_create_models_version([
            prediction['model_info']
            for prediction in model_preds
        ])

        with transaction.atomic():
            draft_entry.clear_data()  # Clear old data if exists
            draft_entry.calculated_at = timezone.now()
            for prediction in model_preds:
                model_version = models_version_map[(prediction['model_info']['id'], prediction['model_info']['version'])]
                cls._process_model_preds(model_version, current_tags_map, draft_entry, prediction)
            draft_entry.save_geo_data()
            draft_entry.save()
        return draft_entry


class LeadExtractionHandler(BaseHandler):
    model = Lead
    callback_url_name = 'lead_extract_callback'

    RETRY_COUNTDOWN = 10 * 60  # 10 min

    @classmethod
    def send_trigger_request_to_extractor(
        cls,
        urls: List[NlpExtractorUrl],
        callback_url: str,
        high_priority=False,
    ):
        payload = {
            'urls': urls,
            'callback_url': callback_url,
            'type': 'user' if high_priority else 'system',
        }
        try:
            response = requests.post(
                DeeplServiceEndpoint.DOCS_EXTRACTOR_ENDPOINT,
                headers=cls.REQUEST_HEADERS,
                data=json.dumps(payload)
            )
            if response.status_code == 200:
                return True
        except Exception:
            logger.error('Lead Extraction Failed, Exception occurred!!', exc_info=True)
        _response = locals().get('response')
        logger.error(
            'Lead Extraction Request Failed!!',
            extra={
                'data': {
                    'payload': payload,
                    'response': _response.content if _response else None
                }
            },
        )

    @classmethod
    def trigger_lead_extract(cls, lead, task_instance=None):
        # No need to process for TEXT source type.
        if lead.source_type == Lead.SourceType.TEXT:
            lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
            return True
        # Get the lead to be extracted
        url_to_extract = None
        if lead.attachment:
            url_to_extract = get_full_media_url(lead.attachment.url)
        elif lead.url:
            url_to_extract = lead.url
        if url_to_extract:
            success = cls.send_trigger_request_to_extractor(
                [
                    {
                        'url': url_to_extract,
                        'client_id': cls.get_client_id(lead),
                    }
                ],
                cls.get_callback_url(),
                high_priority=True,
            )
            if success:
                lead.update_extraction_status(Lead.ExtractionStatus.STARTED)
                return True
        lead.update_extraction_status(Lead.ExtractionStatus.RETRYING)
        if task_instance:
            task_instance.retry(countdown=cls.RETRY_COUNTDOWN)
        return False

    @staticmethod
    def save_data(
        lead: Lead,
        text_source_uri: str,
        images_uri: List[str],
        word_count: int,
        page_count: int,
    ):
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewImage.objects.filter(lead=lead).delete()
        word_count, page_count = word_count, page_count
        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=RequestHelper(url=text_source_uri, ignore_error=True).get_text(sanitize=True) or '',
            word_count=word_count,
            page_count=page_count,
        )
        # Save extracted images as LeadPreviewImage instances
        # TODO: The logic is same for unified_connector leads as well. Maybe have a single func?
        image_base_path = f'{lead.pk}'
        for image_uri in images_uri:
            lead_image = LeadPreviewImage(lead=lead)
            image_obj = RequestHelper(url=image_uri, ignore_error=True).get_file()
            if image_obj:
                lead_image.file.save(
                    os.path.join(image_base_path, os.path.basename(urlparse(image_uri).path)),
                    image_obj
                )
                lead_image.save()
        lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
        return lead

    @staticmethod
    def save_lead_data_using_connector_lead(
        lead: Lead,
        connector_lead: ConnectorLead,
    ):
        if connector_lead.extraction_status != ConnectorLead.ExtractionStatus.SUCCESS:
            return False
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewImage.objects.filter(lead=lead).delete()
        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=connector_lead.simplified_text,
            word_count=connector_lead.word_count,
            page_count=connector_lead.page_count,
        )
        # Save extracted images as LeadPreviewImage instances
        # TODO: The logic is same for unified_connector leads as well. Maybe have a single func?
        for connector_lead_preview_image in connector_lead.preview_images.all():
            lead_image = LeadPreviewImage(lead=lead)
            lead_image.file.save(
                connector_lead_preview_image.image.name,
                connector_lead_preview_image.image,
            )
        lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
        return True


class UnifiedConnectorLeadHandler(BaseHandler):
    model = ConnectorLead
    callback_url_name = 'unified_connector_lead_extract_callback'

    @staticmethod
    def save_data(
        connector_lead: ConnectorLead,
        text_source_uri: str,
        images_uri: List[str],
        word_count: int,
        page_count: int,
    ):
        connector_lead.simplified_text = RequestHelper(url=text_source_uri, ignore_error=True).get_text(sanitize=True) or ''
        connector_lead.word_count = word_count
        connector_lead.page_count = page_count
        image_base_path = f'{connector_lead.pk}'
        for image_uri in images_uri:
            lead_image = ConnectorLeadPreviewImage(connector_lead=connector_lead)
            image_obj = RequestHelper(url=image_uri, ignore_error=True).get_file()
            if image_obj:
                lead_image.image.save(
                    os.path.join(image_base_path, os.path.basename(urlparse(image_uri).path)),
                    image_obj,
                )
                lead_image.save()
        connector_lead.update_extraction_status(ConnectorLead.ExtractionStatus.SUCCESS, commit=False)
        connector_lead.save()
        return connector_lead

    @classmethod
    def _process_unified_source(cls, source):
        params = copy.deepcopy(source.params)
        source_fetcher = source.source_fetcher()
        leads, _ = source_fetcher.get_leads(params, source.created_by)

        current_source_leads_id = set(source.source_leads.values_list('connector_lead_id', flat=True))
        for connector_lead in leads:
            connector_lead, _ = ConnectorLead.get_or_create_from_lead(connector_lead)
            if connector_lead.id not in current_source_leads_id:
                source.add_lead(connector_lead)

    @classmethod
    def _send_trigger_request_to_extraction(cls, connector_leads: List[ConnectorLead]):
        return LeadExtractionHandler.send_trigger_request_to_extractor(
            [
                {
                    'url': connector_lead.url,
                    'client_id': cls.get_client_id(connector_lead),
                }
                for connector_lead in connector_leads
            ],
            cls.get_callback_url(),
            high_priority=False,
        )

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
        if cls._send_trigger_request_to_extraction(connector_leads):  # True if request is successfully send
            extraction_status = ConnectorLead.ExtractionStatus.STARTED
        ConnectorLead.objects\
            .filter(pk__in=[c.pk for c in connector_leads])\
            .update(extraction_status=extraction_status)
        return len(connector_leads)

    @classmethod
    def send_trigger_request_to_extractor(cls, connector_leads_qs: models.QuerySet[ConnectorLead]):
        paginator = Paginator(
            connector_leads_qs.filter(
                extraction_status=ConnectorLead.ExtractionStatus.PENDING
            ).only('id', 'url').order_by('id').distinct(),
            100,
        )
        processed = 0
        while True:
            page = paginator.page(1)
            connector_leads: List[ConnectorLead] = list(page.object_list)
            if not connector_leads:  # Nothing to process anymore
                break
            extraction_status = ConnectorLead.ExtractionStatus.RETRYING
            if cls._send_trigger_request_to_extraction(connector_leads):  # True if request is successfully send
                extraction_status = ConnectorLead.ExtractionStatus.STARTED
            processed += len(connector_leads)
            ConnectorLead.objects\
                .filter(pk__in=[c.pk for c in connector_leads])\
                .update(extraction_status=extraction_status)
        return processed

    @classmethod
    def process_unified_connector_source(cls, source):
        source.status = ConnectorSource.Status.PROCESSING
        source.start_date = timezone.now()
        source.save(update_fields=('status', 'start_date'))
        update_fields = ['status', 'last_fetched_at', 'end_date']
        try:
            # Fetch leads
            cls._process_unified_source(source)
            source.status = ConnectorSource.Status.SUCCESS
            source.generate_stats(commit=False)
            update_fields.append('stats')
        except Exception:
            source.status = ConnectorSource.Status.FAILURE
            logger.error(f'Failed to process source: {source}', exc_info=True)
        source.last_fetched_at = timezone.now()
        source.end_date = timezone.now()
        source.save(update_fields=update_fields)

    @classmethod
    def process_unified_connector(cls, unified_connector_id):
        unified_connector = UnifiedConnector.objects.get(pk=unified_connector_id)
        if not unified_connector.is_active:
            logger.warning(f'Skippping processing for inactive connector (pk:{unified_connector.pk}) {unified_connector}')
            return
        for source in unified_connector.sources.all():
            cls.process_unified_connector_source(source)
        # Send trigger to extractor
        cls.send_trigger_request_to_extractor(
            ConnectorLead.objects.filter(connectorsourcelead__source__unified_connector=unified_connector)
        )
