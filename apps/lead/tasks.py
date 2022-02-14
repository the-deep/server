from typing import List

import time
import os
import re
import requests
import tempfile
import json
import logging

from celery import shared_task
from django.core.files import File
from django.db.models import Q
from django.db.models.functions import Length
from django.conf import settings
from django.utils.encoding import DjangoUnicodeDecodeError

from redis_store import redis
from utils.common import redis_lock, UidBase64Helper
from utils.request import RequestHelper
from utils.extractor.file_document import FileDocument
from utils.extractor.web_document import WebDocument
from utils.extractor.thumbnailers import DocThumbnailer
from .token import lead_extraction_token_generator
from .models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)

logger = logging.getLogger(__name__)

DEEPL_CLASSIFY_URL = settings.DEEPL_API + '/v2/classify/'


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
    def trigger_lead_extract(cls, lead):
    def trigger_lead_extract(cls, lead, task_instance):
        # Get the lead to be extracted
        url_to_extract = None
        if lead.attachment:
            url_to_extract = lead.attachment.url
        elif lead.url:
            url_to_extract = lead.url
        if url_to_extract:
            try:
                payload = {
                    'urls': [
                        {
                            'url': url_to_extract,
                            'client_id': LeadExtraction.generate_lead_client_id(lead.id),
                        }
                    ],
                    'callback_url': settings.DEEPL_EXTRACTOR_CALLBACK_URL
                }
                response = requests.post(
                    settings.DEEPL_EXTRACTOR_URL,
                    headers=cls.REQUEST_HEADERS,
                    data=json.dumps(payload)
                )
                if response.status_code == 200:
                    logger.info('Lead Extraction Request Sent!!', exc_info=True)
                    lead.update_extraction_status(Lead.ExtractionStatus.Started)
                    return True
                else:
                    logger.error('Lead Extraction Request Failed!!', exc_info=True)
            except Exception:
                logger.exception('Lead Extraction Failed, Exception occoured!!', exc_info=True)
        lead.update_extraction_status(Lead.ExtractionStatus.RETRYING)
        task_instance.retry(countdown=cls.RETRY_COUNTDOWN)
        return False

    @staticmethod
    def save_lead_data(
        lead: Lead,
        extraction_success: bool,
        text_source_uri: str,
        images_uri: List[str],
        words_count: int,
        pages_count: int,
    ):
        if not extraction_success:
            lead.update_extraction_status(Lead.ExtractionStatus.FAILED)
            return lead
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewImage.objects.filter(lead=lead).delete()
        word_count, page_count = words_count, pages_count
        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=RequestHelper(url=text_source_uri, ignore_error=True).get_text(),
            word_count=word_count,
            page_count=page_count,
        )
        # Save extracted images as LeadPreviewImage instances
        LeadPreviewImage.objects.filter(lead=lead).delete()
        for image in images_uri:
            lead_image = LeadPreviewImage(lead=lead)
            image_obj = RequestHelper(url=image, ignore_error=True).get_decoded_file()
            if image_obj:
                lead_image.file.save(image_obj.name, image_obj)
                lead_image.save()
        lead.update_extraction_status(Lead.ExtractionStatus.SUCCESS)
        return lead


@shared_task
def extract_thumbnail(lead_id):
    lead = Lead.objects.filter(id=lead_id).first()
    leadPreview = LeadPreview.objects.filter(lead=lead).first()
    thumbnail = None

    if not leadPreview:
        logger.error(
            "Lead preview hasn't been created but extract_thumbnail() called",
            extra={'data': {'lead_id': lead_id}},
        )
        return False

    try:
        if lead.text:
            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(lead.text.encode())
                tmp_file.flush()
                thumbnail = DocThumbnailer(tmp_file, 'txt').get_thumbnail()

        elif lead.attachment:
            doc = FileDocument(
                lead.attachment.file,
                lead.attachment.file.name,
            )
            thumbnail = doc.get_thumbnail()

        elif lead.url:
            doc = WebDocument(lead.url)
            thumbnail = doc.get_thumbnail()

    except Exception:
        logger.error('Lead Extract Thumbnail Failed!!', exc_info=True)

    if thumbnail:
        leadPreview.thumbnail.save(os.path.basename(thumbnail.name),
                                   File(thumbnail), True)
        # Delete thumbnail
        os.unlink(thumbnail.name)


@shared_task
def send_lead_text_to_deepl(lead_id):
    lead = Lead.objects.filter(id=lead_id).first()
    if not lead:
        logger.warning(
            "Lead does not exist but send_lead_text_to_deepl() called.",
            extra={'data': {'lead_id': lead_id}},
        )
        return True

    try:
        return True
        return classify_lead(lead)
    except Exception:
        # Do not retry
        logger.warning("Error while sending request to deepl", exc_info=True)


def classify_lead(lead):
    # NOTE: Just return without making call to DEEPL Server
    logger.info("classify_lead: Returning without making an API call to DEEPL")
    return True
    if lead.project.is_private:
        return True
    # Get preview
    preview = LeadPreview.objects.filter(lead=lead).first()
    if not preview:
        logger.error(
            "Lead preview hasn't been created but send_lead_text_to_deepl() called",
            extra={'data': {'lead_id': lead.id}},
        )
        return False

    preview.classification_status = LeadPreview.ClassificationStatus.INITIATED
    preview.save()
    data = {
        'deeper': 1,
        'group_id': lead.project.id,
        'text': preview.text_extract,
    }
    try:
        response = requests.post(DEEPL_CLASSIFY_URL, data=data)
    except requests.exceptions.ConnectionError:
        preview.classification_status = LeadPreview.ClassificationStatus.FAILED
        preview.save()
        return False
    if response.status_code != 200 and response.status_code != 201:
        preview.classification_status = LeadPreview.ClassificationStatus.ERRORED
        preview.save()
        raise Exception(
            "Status code {} from DEEPL Server response {}".format(
                response.status_code,
                response.text[:300]
            ))
    else:
        response_data = response.json()
        classified_doc_id = response_data.get('id')

        preview.classification_status = LeadPreview.ClassificationStatus.COMPLETED

        preview.classified_doc_id = classified_doc_id
        preview.save()
        return True


@shared_task
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
        extract_from_lead.s(lead_id).delay()
        time.sleep(0.5)


def get_unclassified_leads(limit=10):
    return Lead.objects.filter(
        ~Q(leadpreview=None),
        ~Q(leadpreview__text_extract=None),
        ~Q(leadpreview__text_extract__regex=r'^\W*$'),
        leadpreview__classified_doc_id=None,
        leadpreview__classification_status__in=[
            LeadPreview.ClassificationStatus.FAILED,
            LeadPreview.ClassificationStatus.NONE,
            LeadPreview.ClassificationStatus.INITIATED,
        ],
    ).annotate(
        text_len=Length('leadpreview__text_extract')
    ).filter(
        text_len__lte=5000  # Texts of length 5000 do not pose huge computation in DEEPL
    ).prefetch_related('leadpreview')[:limit]  # Do not get all the previews, do it in a chunk


@shared_task
def classify_remaining_lead_previews():
    """
    Scheduled task(celery beat)
    NOTE: Only use it through schedular
    This looks for previews which do not have classisified doc id
    """
    key = 'classify_remaining_lead_previews'
    lock = redis.get_lock(key, 60 * 60 * 2)  # Lock lifetime 2 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return '{} Locked'.format(key)

    unclassified_leads = get_unclassified_leads(limit=50)

    for lead in unclassified_leads:
        classify_lead(lead)
    return True
