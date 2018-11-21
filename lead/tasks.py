from celery import shared_task
from channels import Group
from django.core.files import File
from django.utils import timezone
from django.conf import settings
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)
from redis_store import redis
from rest_framework.renderers import JSONRenderer
from utils.extractor.file_document import FileDocument
from utils.extractor.web_document import WebDocument
from utils.websocket.subscription import SubscriptionConsumer

import json
import reversion
import os
import re
import requests

import traceback
import logging

logger = logging.getLogger(__name__)

DEEPL_CLASSIFY_URL = settings.DEEPL_API + '/v2/classify/'


def _preprocess(text):
    # Tabs to space
    text = re.sub(r'\t', ' ', text)
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

    with reversion.create_revision():
        text, images = '', []

        # Extract either using FileDocument or WebDocument
        # as per the document type
        try:
            if lead.text:
                text = lead.text
                images = []
            elif lead.attachment:
                text, images = FileDocument(
                    lead.attachment.file,
                    lead.attachment.file.name,
                ).extract()

            elif lead.url:
                text, images = WebDocument(lead.url).extract()

            text = _preprocess(text)
        except Exception:
            logger.error(traceback.format_exc())
            if images:
                for image in images:
                    image.close()
            # return False

        # Save extracted text as LeadPreview
        if text:
            # Classify the text and get doc id

            try:
                data = {
                    'deeper': 1,
                    'group_id': lead.project.id,
                    'text': text,
                }
                response = requests.post(DEEPL_CLASSIFY_URL,
                                         data=data).json()
                classified_doc_id = response.get('id')
            except Exception:
                logger.error(traceback.format_exc())
                classified_doc_id = None

        # Make sure there isn't existing lead preview
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewImage.objects.filter(lead=lead).delete()

        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=text,
            classified_doc_id=classified_doc_id,
        )

        # Save extracted images as LeadPreviewImage instances
        if images:
            LeadPreviewImage.objects.filter(lead=lead).delete()
            for image in images:
                lead_image = LeadPreviewImage(lead=lead)
                lead_image.file.save(os.path.basename(image.name),
                                     File(image), True)
                lead_image.save()
                image.close()

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
    lock = redis.get_lock(key, 60 * 60 * 4)  # Lock lifetime 4 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    try:
        # Actual extraction process
        return_value = _extract_from_lead_core(lead_id)

        # Send signal to all pending websocket clients
        # that the lead extraction has completed.

        code = SubscriptionConsumer.encode({
            'channel': 'leads',
            'event': 'onPreviewExtracted',
            'leadId': lead_id,
        })

        # TODO: Discuss and decide the notification response format
        # Also TODO: Should a handler be added during subscription
        # to immediately reply with already extracted lead?

        Group(code).send(json.loads(
            JSONRenderer().render({
                'code': code,
                'timestamp': timezone.now(),
                'type': 'notification',
                'status': return_value,
            }).decode('utf-8')
        ))
    except Exception:
        logger.error(traceback.format_exc())
        return_value = False

    lock.release()
    return return_value
