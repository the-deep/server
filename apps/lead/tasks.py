from typing import List

import re
import requests
import json
import logging

from celery import shared_task
from django.db.models import Q
from django.conf import settings
from django.urls import reverse

from django.utils.encoding import DjangoUnicodeDecodeError

from utils.common import redis_lock, UidBase64Helper
from utils.request import RequestHelper
from deep.deepl import DeeplServiceEndpoint

from .typings import NlpExtractorUrl
from .token import lead_extraction_token_generator
from .models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)

logger = logging.getLogger(__name__)


# TODO: REMOVE THIS
def _preprocess(text):
    # Remove NUL (0x00) characters
    text = text.replace('\x00', '')
    # Tabs and nbsps to space
    text = re.sub(r'(\t|&nbsp;)', ' ', text)
    # Single line breaks to spaces
    text = re.sub(r'(?<!\n)[ \t]*\n[ \t]*(?!\n)', ' ', text)
    # Multiple spaces to single
    text = re.sub(r' +', ' ', text)
    # More than 3 line breaks to just 3 line breaks
    text = re.sub(r'\n\s*\n\s*(\n\s*)+', '\n\n\n', text)
    return text.strip()


class LeadExtraction:
    REQUEST_HEADERS = {'Content-Type': 'application/json'}
    MAX_RETRIES = 10
    RETRY_COUNTDOWN = 10 * 60  # 10 min

    class Exception():
        class InvalidTokenValue(Exception):
            message = 'Invalid Token'

        class InvalidOrExpiredToken(Exception):
            message = 'Invalid/expired token in client_id'

        class LeadNotFound(Exception):
            message = 'No lead found for provided id'

    @staticmethod
    def get_callback_url():
        return (
            settings.DEEPL_SERVICE_CALLBACK_DOMAIN +
            reverse('lead_extract_callback', kwargs={'version': 'v1'})
        )

    @staticmethod
    def generate_lead_client_id(lead) -> str:
        uid = UidBase64Helper.encode(lead.pk)
        token = lead_extraction_token_generator.make_token(lead)
        return f'{uid}-{token}'

    @classmethod
    def get_lead_from_client_id(cls, client_id):
        try:
            uidb64, token = client_id.split('-', 1)
            uid = UidBase64Helper.decode(uidb64)
        except (ValueError, DjangoUnicodeDecodeError):
            raise cls.Exception.InvalidTokenValue()
        if (lead := Lead.objects.filter(id=uid).first()) is None:
            raise cls.Exception.LeadNotFound(f'No lead found for provided id: {uid}')
        if not lead_extraction_token_generator.check_token(lead, token):
            raise cls.Exception.InvalidOrExpiredToken()
        return lead

    @classmethod
    def send_trigger_request_to_extractor(
        cls,
        urls: List[NlpExtractorUrl],
        callback_url: str,
    ):
        payload = {
            'urls': urls,
            'callback_url': callback_url,
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
            f'Lead Extraction Request Failed!! Response: {_response and _response.content} for payload: {payload}',
            extra={'response': _response and _response.content},
        )

    @classmethod
    def trigger_lead_extract(cls, lead, task_instance):
        # Get the lead to be extracted
        url_to_extract = None
        if lead.attachment:
            url_to_extract = lead.attachment.url
        elif lead.url:
            url_to_extract = lead.url
        if url_to_extract:
            success = cls.send_trigger_request_to_extractor(
                [
                    {
                        'url': url_to_extract,
                        'client_id': LeadExtraction.generate_lead_client_id(lead),
                    }
                ],
                cls.get_callback_url(),
            )
            if success:
                lead.update_extraction_status(Lead.ExtractionStatus.STARTED)
                return True
        lead.update_extraction_status(Lead.ExtractionStatus.RETRYING)
        task_instance.retry(countdown=cls.RETRY_COUNTDOWN)
        return False

    @staticmethod
    def save_lead_data(
        lead: Lead,
        extraction_success: bool,
        text_source_uri: str,
        images_uri: List[str],
        word_count: int,
        page_count: int,
    ):
        if not extraction_success:
            lead.update_extraction_status(Lead.ExtractionStatus.FAILED)
            return lead
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewImage.objects.filter(lead=lead).delete()
        word_count, page_count = word_count, page_count
        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=RequestHelper(url=text_source_uri, ignore_error=True).get_text() or '',
            word_count=word_count,
            page_count=page_count,
        )
        # Save extracted images as LeadPreviewImage instances
        LeadPreviewImage.objects.filter(lead=lead).delete()
        for image in images_uri:
            lead_image = LeadPreviewImage(lead=lead)
            image_obj = RequestHelper(url=image, ignore_error=True).get_file()
            if image_obj:
                lead_image.file.save(image_obj.name, image_obj)
                lead_image.save()
        lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
        return lead


@shared_task(bind=True, max_retries=LeadExtraction.MAX_RETRIES)
@redis_lock('lead_extraction_{0}', 60 * 60 * 0.5)
def extract_from_lead(task_instance, lead_id):
    """
    A task to auto extract text and images from a lead.

    * Lead should have a valid attachment or url.
    * It needs to be checked whether this task from the same lead is already going on.
    """
    try:
        lead = Lead.objects.get(pk=lead_id)
        return LeadExtraction.trigger_lead_extract(lead, task_instance)
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
