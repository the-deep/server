from celery import shared_task
# from channels import Group
from django.core.files import File
from django.db.models import Q
from django.db.models.functions import Length
from django.conf import settings
from lead.models import (
    Lead,
    LeadPreview,
)
from redis_store import redis
# from rest_framework.renderers import JSONRenderer
from utils.extractor.file_document import FileDocument
from utils.extractor.web_document import WebDocument
from utils.extractor.thumbnailers import DocThumbnailer
# from utils.websocket.subscription import SubscriptionConsumer

import time
import os
import re
import requests
import tempfile
import json
import logging
# from utils.websocket.subscription import SubscriptionConsumer

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


def _extract_from_lead_core(lead_id):
    """
    The core lead extraction method.
    DONOT USE THIS METHOD DIRECTLY.
    TO PREVENT MULTIPLE LEAD EXTRACTIONS HAPPEN SIMULTANEOUSLY,
    USE THE extract_from_lead METHOD.
    """
    # Get the lead to be extracted
    lead = Lead.objects.get(id=lead_id)
    url_to_extract = None
    url_content_type = None
    if lead.attachment:
        url_to_extract = lead.attachment.url
        url_content_type = FileDocument(lead.attachment.file, lead.attachment.file.name).type
    elif lead.url:
        url_to_extract = lead.url
        url_content_type = WebDocument(lead.url).type
    if url_to_extract:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "urls": [
                    {
                        "url": url_to_extract,
                        "client_id": lead.id,
                        "url_content_type": url_content_type
                    }
                ],
                "callback_url": settings.DEEPL_EXTRACTOR_CALLBACK_URL
            }
            response = requests.post(settings.DEEPL_EXTRACTOR_URL, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                logger.info('Lead Extraction Request Sent!!', exc_info=True)
            else:
                logger.error('Lead Extraction Request Failed!!', exc_info=True)
        except Exception:
            logger.exception('Lead Extraction Failed, Expeption occoured!!', exc_info=True)
    return True


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
def extract_from_lead(lead_id):
    """
    A task to auto extract text and images from a lead.

    * Lead should have a valid attachment or url.
    * It needs to be checked whether this task from the same lead
      is already going on.
    * On extraction complete, subscribed users through websocket
      need to be notified.
    """

    # Use redis lock to keep track of leads currently being extracted
    # and try to prevent useless parallel extraction of same lead that
    # that might happen.
    key = 'lead_extraction_{}'.format(lead_id)
    lock = redis.get_lock(key, 60 * 60 * 0.5)  # Lock lifetime half hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    try:
        # Actual extraction process
        return_value = _extract_from_lead_core(lead_id)

        # Send signal to all pending websocket clients
        # that the lead extraction has completed.

        # code = SubscriptionConsumer.encode({
        #     'channel': 'leads',
        #     'event': 'onPreviewExtracted',
        #     'leadId': lead_id,
        # })

        # TODO: Discuss and decide the notification response format
        # Also TODO: Should a handler be added during subscription
        # to immediately reply with already extracted lead?

        # Group(code).send(json.loads(
        #     JSONRenderer().render({
        #         'code': code,
        #         'timestamp': timezone.now(),
        #         'type': 'notification',
        #         'status': return_value,
        #     }).decode('utf-8')
        # ))
    except Exception:
        logger.error('Lead Core Extraction Failed!!', exc_info=True)
        return_value = False

    lock.release()
    return return_value


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
