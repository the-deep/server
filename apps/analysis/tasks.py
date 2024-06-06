import logging

from celery import shared_task
from django.db import models
from lead.models import Lead

from utils.files import generate_json_file_for_upload
from deepl_integration.handlers import (
    AnalysisTopicModelHandler,
    AnalysisAutomaticSummaryHandler,
    AnalyticalStatementNGramHandler,
    AnalyticalStatementGeoHandler,
)

from entry.models import Entry
from .models import (
    TopicModel,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
)

logger = logging.getLogger(__name__)


@shared_task
def trigger_topic_model(_id):
    topic_model = TopicModel.objects.get(pk=_id)
    # Generate entries data file
    entries_id_qs = list(
        topic_model
        .get_entries_qs()
        .exclude(excerpt='')
        # TODO: Use original? dropped_excerpt
        # This is the format which deepl expects
        # https://docs.google.com/document/d/1NmjOO5sOrhJU6b4QXJBrGAVk57_NW87mLJ9wzeY_NZI/edit#heading=h.cif9hh69nfvz
        .values('excerpt', entry_id=models.F('id'))
    )
    payload = {
        'data': entries_id_qs,
        'tags': topic_model.widget_tags,
    }
    topic_model.entries_file.save(
        f'{topic_model.id}.json',
        generate_json_file_for_upload(payload),
    )
    # Send trigger request
    AnalysisTopicModelHandler.send_trigger_request_to_extractor(topic_model)
    # Send trigger process in deepl


@shared_task
def trigger_automatic_summary(_id):
    a_summary = AutomaticSummary.objects.get(pk=_id)
    entries_data = list(
        Entry.objects.filter(
            project=a_summary.project,
            id__in=a_summary.entries_id,
            lead__confidentiality=Lead.Confidentiality.UNPROTECTED,
        ).values('excerpt', entry_id=models.F('id'))
    )
    payload = {
        'data': entries_data,
        'tags': a_summary.widget_tags,
    }
    a_summary.entries_file.save(
        f'{a_summary.id}.json',
        generate_json_file_for_upload(payload),
    )
    AnalysisAutomaticSummaryHandler.send_trigger_request_to_extractor(a_summary)


@shared_task
def trigger_automatic_ngram(_id):
    a_ngram = AnalyticalStatementNGram.objects.get(pk=_id)
    entries_data = list(
        Entry.objects.filter(
            project=a_ngram.project,
            id__in=a_ngram.entries_id,
        ).values('excerpt', entry_id=models.F('id'))
    )
    a_ngram.entries_file.save(
        f'{a_ngram.id}.json',
        generate_json_file_for_upload(entries_data),
    )
    AnalyticalStatementNGramHandler.send_trigger_request_to_extractor(a_ngram)


@shared_task
def trigger_geo_location(_id):
    geo_location_task = AnalyticalStatementGeoTask.objects.get(pk=_id)
    entries_data = list(
        Entry.objects.filter(
            project=geo_location_task.project,
            id__in=geo_location_task.entries_id,
        ).values('excerpt', entry_id=models.F('id'))
    )
    geo_location_task.entries_file.save(
        f'{geo_location_task.id}.json',
        generate_json_file_for_upload(entries_data),
    )
    AnalyticalStatementGeoHandler.send_trigger_request_to_extractor(geo_location_task)
