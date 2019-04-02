from celery import shared_task
# from channels import Group
from django.core.files import File
from django.db import transaction
from django.db.models import Q
# from django.utils import timezone
from django.conf import settings
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)
from redis_store import redis
# from rest_framework.renderers import JSONRenderer
from utils.extractor.file_document import FileDocument
from utils.extractor.web_document import WebDocument
from utils.extractor.thumbnailers import DocThumbnailer
# from utils.websocket.subscription import SubscriptionConsumer

import time
import reversion
import os
import re
import requests
import tempfile

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
        word_count, page_count = 0, 1

        # Extract either using FileDocument or WebDocument
        # as per the document type
        try:
            if lead.text:
                text = lead.text
                images = []

            elif lead.attachment:
                doc = FileDocument(
                    lead.attachment.file,
                    lead.attachment.file.name,
                )
                text, images, page_count = doc.extract()

            elif lead.url:
                doc = WebDocument(lead.url)
                text, images, page_count = doc.extract()

            text = _preprocess(text)
            word_count = len(re.findall(r'\b\S+\b', text))
        except Exception:
            logger.error(traceback.format_exc())
            if images:
                for image in images:
                    image.close()
            # return False

        # Make sure there isn't existing lead preview
        LeadPreview.objects.filter(lead=lead).delete()
        LeadPreviewImage.objects.filter(lead=lead).delete()

        # and create new one
        LeadPreview.objects.create(
            lead=lead,
            text_extract=text,
            word_count=word_count,
            page_count=page_count,
        )

        transaction.on_commit(
            lambda: extract_thumbnail.s(lead.id).delay()
        )
        if text:
            # Send background deepl request
            transaction.on_commit(
                lambda: send_lead_text_to_deepl.s(lead.id).delay()
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
def extract_thumbnail(lead_id):
    lead = Lead.objects.filter(id=lead_id).first()
    leadPreview = LeadPreview.objects.filter(lead=lead).first()
    thumbnail = None

    if not leadPreview:
        logger.error(
            "Lead(id:{}) preview hasn't been created but extract_thumbnail() called".  # noqa
            format(lead_id)
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
        logger.error(traceback.format_exc())

    if thumbnail:
        leadPreview.thumbnail.save(os.path.basename(thumbnail.name),
                                   File(thumbnail), True)
        # Delete thumbnail
        os.unlink(thumbnail.name)


@shared_task(bind=True, max_retries=10)
def send_lead_text_to_deepl(self, lead_id):
    lead = Lead.objects.filter(id=lead_id).first()
    if not lead:
        logger.warning(
            "Lead(id:{}) does not exist but send_lead_text_to_deepl() called.".
            format(lead_id)
        )
        return True

    # Get preview
    preview = LeadPreview.objects.filter(lead=lead).first()
    if not preview:
        logger.error(
            "Lead(id:{}) preview hasn't been created but send_lead_text_to_deepl() called".  # noqa
            format(lead_id)
        )
        return False

    try:
        data = {
            'deeper': 1,
            'group_id': lead.project.id,
            'text': preview.text_extract,
        }
        response = requests.post(DEEPL_CLASSIFY_URL,
                                 data=data)
        response_data = response.json()
        classified_doc_id = response_data.get('id')

        preview.classified_doc_id = classified_doc_id
        preview.save()
        return True
    except Exception:
        # Retry with exponential decay
        logger.warning("Error while sending request to deepl. {}".format(
            traceback.format_exc()))
        retry_countdown = 2 ** self.request.retries
        self.retry(countdown=retry_countdown)


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
        logger.error(traceback.format_exc())
        return_value = False

    lock.release()
    return return_value


@shared_task
def generate_previews(lead_ids=None):
    """Generae previews of leads which do not have preview"""
    print('here in generate_preview')
    lead_ids = lead_ids or Lead.objects.filter(
        Q(leadpreview__isnull=True) |
        Q(leadpreview__text_extract=''),
    ).values_list('id', flat=True)

    for lead_id in lead_ids:
        extract_from_lead.s(lead_id).delay()
        time.sleep(0.5)
