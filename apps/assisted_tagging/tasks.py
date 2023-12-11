from django.conf import settings
import logging
import requests
import json

from celery import shared_task
from lead.models import Lead

from utils.common import redis_lock
from deep.deepl import DeeplServiceEndpoint
from deepl_integration.handlers import AssistedTaggingDraftEntryHandler, AutoAssistedTaggingDraftEntryHandler

from .models import (
    DraftEntry,
    AssistedTaggingModel,
    AssistedTaggingModelVersion,
    AssistedTaggingModelPredictionTag,
)


logger = logging.getLogger(__name__)


def sync_tags_with_deepl():
    def _get_existing_tags_by_tagid():
        return {
            tag.tag_id: tag  # tag_id is from deepl
            for tag in AssistedTaggingModelPredictionTag.objects.all()
        }

    headers = {'Authorization': f'Token {settings.DEEPL_SERVER_TOKEN}'}
    response = requests.get(DeeplServiceEndpoint.ASSISTED_TAGGING_TAGS_ENDPOINT, headers=headers).json()
    existing_tags_by_tagid = _get_existing_tags_by_tagid()

    new_tags = []
    updated_tags = []
    for tag_id, tag_meta in response.items():
        assisted_tag = existing_tags_by_tagid.get(tag_id, AssistedTaggingModelPredictionTag())
        assisted_tag.name = tag_meta['label']
        assisted_tag.group = tag_meta.get('group')
        assisted_tag.is_category = tag_meta['is_category']
        assisted_tag.hide_in_analysis_framework_mapping = tag_meta['hide_in_analysis_framework_mapping']
        if assisted_tag.id:
            updated_tags.append(assisted_tag)
        else:
            assisted_tag.tag_id = tag_id
            new_tags.append(assisted_tag)

    if new_tags:
        AssistedTaggingModelPredictionTag.objects.bulk_create(new_tags)
    if updated_tags:
        AssistedTaggingModelPredictionTag.objects.bulk_update(
            updated_tags,
            fields=(
                'name',
                'is_category',
                'group',
                'hide_in_analysis_framework_mapping',
            )
        )

    # For parent relation
    updated_tags = []
    existing_tags_by_tagid = _get_existing_tags_by_tagid()
    for tag_id, tag_meta in response.items():
        if tag_meta.get('parent_id') is None:
            continue
        assisted_tag = existing_tags_by_tagid[tag_id]
        parent_tag = existing_tags_by_tagid[tag_meta['parent_id']]
        if parent_tag.pk == assisted_tag.parent_tag_id:
            continue
        assisted_tag.parent_tag = parent_tag
        updated_tags.append(assisted_tag)
    if updated_tags:
        AssistedTaggingModelPredictionTag.objects.bulk_update(
            updated_tags,
            fields=('parent_tag',)
        )


def sync_models_with_deepl():
    models_data = requests.get(DeeplServiceEndpoint.ASSISTED_TAGGING_MODELS_ENDPOINT).json()
    for model_meta in models_data.values():
        assisted_model, _ = AssistedTaggingModel.objects.get_or_create(
            model_id=model_meta['id'],
        )
        AssistedTaggingModelVersion.objects.get_or_create(
            model=assisted_model,
            version=model_meta['version'],
        )


@shared_task
@redis_lock('trigger_request_for_draft_entry_task_{0}', 60 * 60 * 0.5)
def trigger_request_for_draft_entry_task(draft_entry_id):
    draft_entry = DraftEntry.objects.get(pk=draft_entry_id)
    return AssistedTaggingDraftEntryHandler.send_trigger_request_to_extractor(draft_entry)


@shared_task
@redis_lock('trigger_request_for_auto_draft_entry_task_{0}', 60 * 60 * 0.5)
def trigger_request_for_auto_draft_entry_task(lead):
    lead = Lead.objects.get(id=lead)
    return AutoAssistedTaggingDraftEntryHandler.auto_trigger_request_to_extractor(lead)


@shared_task
@redis_lock('sync_tags_with_deepl_task', 60 * 60 * 0.5)
def sync_tags_with_deepl_task():
    return (
        sync_tags_with_deepl(),
        sync_models_with_deepl(),
    )
