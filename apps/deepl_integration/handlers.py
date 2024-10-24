import os
import json
import copy
import requests
import logging
from typing import Dict, List, Type
from functools import reduce
from urllib.parse import urlparse

from django.conf import settings
from django.urls import reverse
from django.utils.encoding import DjangoUnicodeDecodeError
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction, models
from rest_framework import serializers

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
    ConnectorLeadPreviewAttachment,
    ConnectorSource,
    UnifiedConnector,
)
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewAttachment,
)
from lead.typings import NlpExtractorDocument
from entry.models import Entry
from analysis.models import (
    TopicModel,
    TopicModelCluster,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
    AnalyticalStatementGeoEntry,
)
from geo.models import GeoArea
from geo.filter_set import GeoAreaGqlFilterSet

from .models import DeeplTrackBaseModel


logger = logging.getLogger(__name__)


def generate_file_url_for_legacy_deepl_server(file):
    return get_full_media_url(
        file.url,
        file_system_domain=settings.DEEPL_SERVICE_CALLBACK_DOMAIN,
    )


def generate_file_url_for_new_deepl_server(file):
    return get_full_media_url(
        file.url,
        file_system_domain=settings.DEEPL_SERVER_CALLBACK_DOMAIN,
    )


def custom_error_handler(exception, url=None):
    if isinstance(exception, requests.exceptions.ConnectionError):
        raise serializers.ValidationError(f'ConnectionError on provided file: {url}')
    if isinstance(exception, json.decoder.JSONDecodeError):
        raise serializers.ValidationError(f'Failed to parse provided json file: {url}')
    raise serializers.ValidationError(f'Failed to handle the provided file: <error={type(exception)}>: {url}')


class DefaultClientIdGenerator(DeepTokenGenerator):
    key_salt = "deepl-integration-callback-client-id"

    def _make_hash_value(self, instance, timestamp):
        return str(type(instance)) + str(instance.pk) + str(timestamp)


class NlpRequestType:
    SYSTEM = 0  # Note: SYSTEM refers to requests from CONNECTORS.
    USER = 1


class BaseHandler:
    REQUEST_HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {settings.DEEPL_SERVER_TOKEN}',
    }

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
        response_content = None
        try:
            response = requests.post(
                DeeplServiceEndpoint.ASSISTED_TAGGING_ENTRY_PREDICT_ENDPOINT,
                headers=cls.REQUEST_HEADERS,
                json=payload
            )
            response_content = response.content
            if response.status_code == 202:
                return True
        except Exception:
            logger.error('Assisted tagging send failed, Exception occurred!!', exc_info=True)
            draft_entry.prediction_status = DraftEntry.PredictionStatus.SEND_FAILED
            draft_entry.save(update_fields=('prediction_status',))
        logger.error(
            'Assisted tagging send failed!!',
            extra={
                'data': {
                    'payload': payload,
                    'response': response_content,
                },
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
            tag
            for tag in tags
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
        if not prediction_status:  # If False no tags are provided
            return

        tags = model_prediction.get('model_tags', {})  # NLP TagId
        values = model_prediction.get('values', [])  # Raw value

        common_attrs = dict(
            model_version=model_version,
            draft_entry_id=draft_entry.id,
        )
        new_predictions = []
        for category_tag, tags in tags.items():
            for tag, prediction_data in tags.items():
                prediction_value = prediction_data.get('prediction')
                threshold_value = prediction_data.get('threshold')
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
        model_preds = data
        # Save if new tags are provided
        current_tags_map = cls._get_or_create_tags_map([
            tag
            for category_tag, tags in model_preds['model_tags'].items()
            for tag in [
                category_tag,
                *tags.keys(),
            ]
        ])
        models_version_map = cls._get_or_create_models_version(
            [
                model_preds['model_info']
            ]
        )
        with transaction.atomic():
            draft_entry.clear_data()  # Clear old data if exists
            draft_entry.calculated_at = timezone.now()
            model_version = models_version_map[(model_preds['model_info']['id'], model_preds['model_info']['version'])]
            cls._process_model_preds(model_version, current_tags_map, draft_entry, model_preds)
            draft_entry.prediction_status = DraftEntry.PredictionStatus.DONE
            draft_entry.save_geo_data()
            draft_entry.save()
        return draft_entry


class AutoAssistedTaggingDraftEntryHandler(BaseHandler):
    # TODO: Fix N+1 issues here. Try to do bulk_update for each models.
    # Or do this Async
    model = Lead
    callback_url_name = 'auto-assisted_tagging_draft_entry_prediction_callback'

    @classmethod
    def auto_trigger_request_to_extractor(cls, lead):
        lead_preview = LeadPreview.objects.get(lead=lead)
        payload = {
            "documents": [
                {
                    "client_id": cls.get_client_id(lead),
                    "text_extraction_id": str(lead_preview.text_extraction_id),
                }
            ],
            "callback_url": cls.get_callback_url()
        }
        response_content = None
        try:
            response = requests.post(
                url=DeeplServiceEndpoint.ENTRY_EXTRACTION_CLASSIFICATION,
                headers=cls.REQUEST_HEADERS,
                json=payload
            )
            response_content = response.content
            if response.status_code == 202:
                lead.auto_entry_extraction_status = Lead.AutoExtractionStatus.PENDING
                lead.save(update_fields=('auto_entry_extraction_status',))
                return True

        except Exception:
            logger.error('Entry Extraction send failed, Exception occurred!!', exc_info=True)
            lead.auto_entry_extraction_status = Lead.AutoExtractionStatus.FAILED
            lead.save(update_fields=('auto_entry_extraction_status',))
        logger.error(
            'Entry Extraction send failed!!',
            extra={
                'data': {
                    'payload': payload,
                    'response': response_content,
                },
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
                                model__model_id=model_data['name'],
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
            if (model_data['name'], model_data['version']) not in existing_model_versions
        ]

        if new_model_versions:
            AssistedTaggingModelVersion.objects.bulk_create([
                AssistedTaggingModelVersion(
                    model=AssistedTaggingModel.objects.get_or_create(
                        model_id=model_data['name'],
                        defaults=dict(
                            name=model_data['name'],
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
            tag
            for tag in tags
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
        if not prediction_status:  # If False  no tags are provided
            return

        tags = model_prediction.get('classification', {})  # NLP TagId
        values = model_prediction.get('values', [])  # Raw value

        common_attrs = dict(
            model_version=model_version,
            draft_entry_id=draft_entry.id,
        )
        new_predictions = []
        for category_tag, tags in tags.items():
            for tag, prediction_data in tags.items():
                prediction_value = prediction_data.get('prediction')
                threshold_value = prediction_data.get('threshold')
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
    @transaction.atomic
    def save_data(cls, lead, data_url):
        # NOTE: Schema defined here
        # - https://docs.google.com/document/d/1NmjOO5sOrhJU6b4QXJBrGAVk57_NW87mLJ9wzeY_NZI/edit#heading=h.t3u7vdbps5pt
        data = RequestHelper(url=data_url, ignore_error=True).json()
        draft_entry_qs = DraftEntry.objects.filter(lead=lead, type=DraftEntry.Type.AUTO)
        if draft_entry_qs.exists():
            raise serializers.ValidationError('Draft entries already exit')
        for model_preds in data['blocks']:
            if not model_preds['relevant']:
                continue
            classification = model_preds['classification']
            current_tags_map = cls._get_or_create_tags_map([
                tag
                for category_tag, tags in classification.items()
                for tag in [
                    category_tag,
                    *tags.keys(),
                ]
            ])
            models_version_map = cls._get_or_create_models_version([
                data['classification_model_info']
            ])
            draft = DraftEntry.objects.create(
                page=model_preds['page'],
                text_order=model_preds['textOrder'],
                project=lead.project,
                lead=lead,
                excerpt=model_preds['text'],
                prediction_status=DraftEntry.PredictionStatus.DONE,
                type=DraftEntry.Type.AUTO
            )
            if model_preds['geolocations']:
                geo_areas_qs = GeoAreaGqlFilterSet(
                    data={'titles': [geo['entity'] for geo in model_preds['geolocations']]},
                    queryset=GeoArea.get_for_project(lead.project)
                ).qs.distinct('title')
                draft.related_geoareas.set(geo_areas_qs)
            model_version = models_version_map[
                (data['classification_model_info']['name'], data['classification_model_info']['version'])
            ]
            cls._process_model_preds(model_version, current_tags_map, draft, model_preds)
        lead.auto_entry_extraction_status = Lead.AutoExtractionStatus.SUCCESS
        lead.save(update_fields=('auto_entry_extraction_status',))
        return lead


class LeadExtractionHandler(BaseHandler):
    model = Lead
    callback_url_name = 'lead_extract_callback'

    RETRY_COUNTDOWN = 10 * 60  # 10 min

    @classmethod
    def send_trigger_request_to_extractor(
        cls,
        documents: List[NlpExtractorDocument],
        callback_url: str,
        high_priority=False,
    ):
        payload = {
            'documents': documents,
            'callback_url': callback_url,
            'request_type': NlpRequestType.USER if high_priority else NlpRequestType.SYSTEM,
        }
        response_content = None
        try:
            response = requests.post(
                DeeplServiceEndpoint.DOCS_EXTRACTOR_ENDPOINT,
                headers=cls.REQUEST_HEADERS,
                data=json.dumps(payload)
            )
            response_content = response.content
            if response.status_code == 202:
                return True
        except Exception:
            logger.error('Lead Extraction Failed, Exception occurred!!', exc_info=True)
        logger.error(
            'Lead Extraction Request Failed!!',
            extra={
                'data': {
                    'payload': payload,
                    'response': response_content
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
            url_to_extract = generate_file_url_for_legacy_deepl_server(lead.attachment)
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
        images_uri: List[dict],
        table_uri: List[dict],
        word_count: int,
        page_count: int,
        text_extraction_id: str,
    ):
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewAttachment.objects.filter(lead=lead).delete()
        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=RequestHelper(url=text_source_uri, ignore_error=True).get_text(sanitize=True) or '',
            word_count=word_count,
            page_count=page_count,
            text_extraction_id=text_extraction_id,
        )
        # Save extracted images as LeadPreviewAttachment instances
        # TODO: The logic is same for unified_connector leads as well. Maybe have a single func?

        attachment_base_path = f'{lead.pk}'
        for image_uri in images_uri:
            for image in image_uri['images']:
                image_obj = RequestHelper(url=image, ignore_error=True).get_file()
                if image_obj:
                    lead_attachment = LeadPreviewAttachment(lead=lead)
                    lead_attachment.file.save(
                        os.path.join(
                            attachment_base_path,
                            os.path.basename(
                                urlparse(image).path
                            )
                        ),
                        image_obj,
                    )
                    lead_attachment.page_number = image_uri['page_number']
                    lead_attachment.type = LeadPreviewAttachment.AttachmentFileType.IMAGE
                    lead_attachment.file_preview = lead_attachment.file
                    lead_attachment.save()

        for table in table_uri:
            table_img = RequestHelper(url=table['image_link'], ignore_error=True).get_file()
            table_attachment = RequestHelper(url=table['content_link'], ignore_error=True).get_file()
            if table_img:
                lead_attachment = LeadPreviewAttachment(lead=lead)
                lead_attachment.file_preview.save(
                    os.path.join(
                        attachment_base_path,
                        os.path.basename(
                            urlparse(table['image_link']).path
                        )
                    ),
                    table_img,
                )
                lead_attachment.page_number = table['page_number']
                lead_attachment.type = LeadPreviewAttachment.AttachmentFileType.XLSX
                lead_attachment.file.save(
                    os.path.join(
                        attachment_base_path,
                        os.path.basename(
                            urlparse(table['content_link']).path
                        )
                    ),
                    table_attachment,
                )
                lead_attachment.save()

        lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
        return lead

    @staticmethod
    @transaction.atomic
    def save_lead_data_using_connector_lead(
        lead: Lead,
        connector_lead: ConnectorLead,
    ):
        if connector_lead.extraction_status != ConnectorLead.ExtractionStatus.SUCCESS:
            return False
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewAttachment.objects.filter(lead=lead).delete()
        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=connector_lead.simplified_text,
            word_count=connector_lead.word_count,
            page_count=connector_lead.page_count,
            text_extraction_id=connector_lead.text_extraction_id,
        )
        # Save extracted images as LeadPreviewAttachment instances
        # TODO: The logic is same for unified_connector leads as well. Maybe have a single func?
        for connector_lead_attachment in connector_lead.preview_images.all():
            lead_attachment = LeadPreviewAttachment(lead=lead)
            lead_attachment.order = connector_lead_attachment.order
            lead_attachment.file.save(
                connector_lead_attachment.file.name,
                connector_lead_attachment.file,
            )
            lead_attachment.file_preview.save(
                connector_lead_attachment.file_preview.name,
                connector_lead_attachment.file_preview
            )
            lead_attachment.save()
        lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
        return True


class UnifiedConnectorLeadHandler(BaseHandler):
    model = ConnectorLead
    callback_url_name = 'unified_connector_lead_extract_callback'

    @staticmethod
    def save_data(
        connector_lead: ConnectorLead,
        text_source_uri: str,
        images_uri: List[Dict],
        table_uri: List[Dict],
        word_count: int,
        page_count: int,
        text_extraction_id: str,
    ):
        connector_lead.simplified_text = RequestHelper(url=text_source_uri, ignore_error=True).get_text(sanitize=True) or ''
        connector_lead.word_count = word_count
        connector_lead.page_count = page_count
        connector_lead.text_extraction_id = text_extraction_id

        attachment_base_path = f'{connector_lead.pk}'
        for image_uri in images_uri:
            for image in image_uri['images']:
                image_obj = RequestHelper(url=image, ignore_error=True).get_file()
                if image_obj:
                    connector_lead_attachment = ConnectorLeadPreviewAttachment(connector_lead=connector_lead)
                    connector_lead_attachment.file.save(
                        os.path.join(
                            attachment_base_path,
                            os.path.basename(
                                urlparse(image).path
                            )
                        ),
                        image_obj,
                    )
                    connector_lead_attachment.page_number = image_uri['page_number']
                    connector_lead_attachment.type = ConnectorLeadPreviewAttachment.ConnectorAttachmentFileType.IMAGE
                    connector_lead_attachment.file_preview = connector_lead_attachment.file
                    connector_lead_attachment.save()

        for table in table_uri:
            table_img = RequestHelper(url=table['image_link'], ignore_error=True).get_file()
            table_attachment = RequestHelper(url=table['content_link'], ignore_error=True).get_file()
            if table_img:
                connector_lead_attachment = ConnectorLeadPreviewAttachment(connector_lead=connector_lead)
                connector_lead_attachment.file_preview.save(
                    os.path.join(
                        attachment_base_path,
                        os.path.basename(
                            urlparse(table['image_link']).path
                        )
                    ),
                    table_img,
                )
                connector_lead_attachment.page_number = table['page_number']
                connector_lead_attachment.type = ConnectorLeadPreviewAttachment.ConnectorAttachmentFileType.XLSX
                connector_lead_attachment.file.save(
                    os.path.join(
                        attachment_base_path,
                        os.path.basename(
                            urlparse(table['content_link']).path
                        )
                    ),
                    table_attachment,
                )
                connector_lead_attachment.save()

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
        if connector_leads:
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
        # All good for empty connector_leads
        return True

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
            # Why use 1?
            # As we are updating ConnectorLead, we need to stay at page 1 to get the next set of data
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


class NewNlpServerBaseHandler(BaseHandler):
    model: Type[DeeplTrackBaseModel]
    endpoint: str

    @classmethod
    def get_callback_url(cls, **kwargs):
        return (
            settings.DEEPL_SERVER_CALLBACK_DOMAIN +
            reverse(
                cls.callback_url_name, kwargs={
                    'version': 'v1',
                    **kwargs,
                },
            )
        )

    @classmethod
    def get_trigger_payload(cls, _: DeeplTrackBaseModel) -> dict:
        return {}

    @classmethod
    def send_trigger_request_to_extractor(cls, obj: DeeplTrackBaseModel):
        # Base payload attributes
        payload = {
            'mock': settings.DEEPL_SERVER_AS_MOCK,
            'client_id': cls.get_client_id(obj),
            'callback_url': cls.get_callback_url(),
        }
        # Additional payload attributes
        payload.update(
            cls.get_trigger_payload(obj)
        )

        try:
            response = requests.post(
                cls.endpoint,
                headers=cls.REQUEST_HEADERS,
                json=payload,
            )
            if response.status_code == 202:
                obj.status = cls.model.Status.STARTED
                obj.save(update_fields=('status',))
                return True
        except Exception:
            logger.error(f'{cls.model.__name__} send failed, Exception occurred!!', exc_info=True)
        _response = locals().get('response')
        error_extra_context = {
            'payload': payload,
        }
        if _response is not None:
            error_extra_context.update({
                'response': _response.content,
                'response_status_code': _response.status_code,
            })
        logger.error(
            f'{cls.model.__name__} send failed!!',
            extra={
                'data': {
                    'context': error_extra_context
                }
            }
        )
        obj.status = cls.model.Status.SEND_FAILED
        obj.save(update_fields=('status',))


class AnalysisTopicModelHandler(NewNlpServerBaseHandler):
    model = TopicModel
    endpoint = DeeplServiceEndpoint.ANALYSIS_TOPIC_MODEL
    callback_url_name = 'analysis_topic_model_callback'

    @classmethod
    def get_trigger_payload(cls, obj: TopicModel):
        return {
            'entries_url': generate_file_url_for_new_deepl_server(obj.entries_file),
            'cluster_size': settings.ANALYTICAL_ENTRIES_COUNT,
            'max_clusters_num': settings.ANALYTICAL_STATEMENT_COUNT,
        }

    @staticmethod
    def save_data(
        topic_model: TopicModel,
        data: dict,
    ):
        data_url = data['presigned_s3_url']
        entries_data = RequestHelper(url=data_url, custom_error_handler=custom_error_handler).json()
        if entries_data:
            # Clear existing
            TopicModelCluster.objects.filter(topic_model=topic_model).delete()
            # Create new cluster in bulk
            new_clusters = TopicModelCluster.objects.bulk_create([
                TopicModelCluster(topic_model=topic_model, title=_['label'])
                for _ in entries_data.values()
            ])
            # Create new cluster-entry relation in bulk
            new_cluster_entries = []
            for cluster, entries_id in zip(new_clusters, entries_data.values()):
                for entry_id in entries_id['entry_id']:
                    new_cluster_entries.append(
                        TopicModelCluster.entries.through(
                            topicmodelcluster=cluster,
                            entry_id=entry_id,
                        ),
                    )
            TopicModelCluster.entries.through.objects.bulk_create(new_cluster_entries, ignore_conflicts=True)
        topic_model.status = TopicModel.Status.SUCCESS
        topic_model.save()


class AnalysisAutomaticSummaryHandler(NewNlpServerBaseHandler):
    model = AutomaticSummary
    endpoint = DeeplServiceEndpoint.ANALYSIS_AUTOMATIC_SUMMARY
    callback_url_name = 'analysis_automatic_summary_callback'

    @classmethod
    def get_trigger_payload(cls, obj: AutomaticSummary):
        return {
            'entries_url': generate_file_url_for_new_deepl_server(obj.entries_file),
        }

    @staticmethod
    def save_data(
        a_summary: AutomaticSummary,
        data: dict,
    ):
        data_url = data['presigned_s3_url']
        summary_data = RequestHelper(url=data_url, custom_error_handler=custom_error_handler).json()
        a_summary.status = AutomaticSummary.Status.SUCCESS
        a_summary.summary = summary_data.get('summary', '')
        a_summary.analytical_statement = summary_data.get('analytical_statement', '')
        a_summary.information_gap = summary_data.get('info_gaps', '')

        a_summary.save()


class AnalyticalStatementNGramHandler(NewNlpServerBaseHandler):
    model = AnalyticalStatementNGram
    endpoint = DeeplServiceEndpoint.ANALYSIS_AUTOMATIC_NGRAM
    callback_url_name = 'analysis_automatic_ngram_callback'

    @classmethod
    def get_trigger_payload(cls, obj: AnalyticalStatementNGram):
        return {
            'entries_url': generate_file_url_for_new_deepl_server(obj.entries_file),
            'ngrams_config': {},
        }

    @staticmethod
    def save_data(
        a_ngram: AnalyticalStatementNGram,
        data: dict,
    ):
        data_url = data['presigned_s3_url']
        ngram_data = RequestHelper(url=data_url, custom_error_handler=custom_error_handler).json()
        if ngram_data:
            a_ngram.unigrams = ngram_data.get('unigrams') or {}
            a_ngram.bigrams = ngram_data.get('bigrams') or {}
            a_ngram.trigrams = ngram_data.get('trigrams') or {}
        a_ngram.status = AnalyticalStatementNGram.Status.SUCCESS
        a_ngram.save()


class AnalyticalStatementGeoHandler(NewNlpServerBaseHandler):
    model = AnalyticalStatementGeoTask
    endpoint = DeeplServiceEndpoint.ANALYSIS_GEO
    callback_url_name = 'analysis_geo_callback'

    @classmethod
    def get_trigger_payload(cls, obj: AnalyticalStatementNGram):
        return {
            'entries_url': generate_file_url_for_new_deepl_server(obj.entries_file),
        }

    @staticmethod
    def save_data(
        geo_task: AnalyticalStatementGeoTask,
        data: dict,
    ):
        data_url = data['presigned_s3_url']
        geo_data = RequestHelper(url=data_url, custom_error_handler=custom_error_handler).json()
        if geo_data is not None:
            geo_entry_objs = []
            # Clear out existing
            AnalyticalStatementGeoEntry.objects.filter(
                task=geo_task
            ).delete()
            existing_entries_id = set(
                Entry.objects.filter(
                    project=geo_task.project,
                    id__in=[
                        int(entry_geo_data['entry_id'])
                        for entry_geo_data in geo_data
                    ]
                ).values_list('id', flat=True)
            )
            for entry_geo_data in geo_data:
                entry_id = int(entry_geo_data['entry_id'])
                data = entry_geo_data.get('locations')
                if data and entry_id in existing_entries_id:
                    geo_entry_objs.append(
                        AnalyticalStatementGeoEntry(
                            task=geo_task,
                            entry_id=entry_id,
                            data=data,
                        )
                    )
            # Save all in bulk
            AnalyticalStatementGeoEntry.objects.bulk_create(geo_entry_objs, ignore_conflicts=True)
            geo_task.status = AnalyticalStatementGeoTask.Status.SUCCESS
        else:
            geo_task.status = AnalyticalStatementGeoTask.Status.FAILED
        geo_task.save(update_fields=('status',))
