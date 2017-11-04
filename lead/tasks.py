from celery import shared_task
from channels import Group
from django.core.files import File
from django.utils import timezone
from lead.models import (
    Lead,
    LeadPreview,
    LeadPreviewImage,
)
from redis_store import redis
from rest_framework.renderers import JSONRenderer
from utils.extractors.file_document import FileDocument
from utils.extractors.web_document import WebDocument
from utils.websocket.subscription import SubscriptionConsumer

import json
import reversion
import os


def _extract_from_lead_core(lead):
    """
    The core lead extraction method.
    DONOT USE THIS METHOD DIRECTLY.
    TO PREVENT MULTIPLE LEAD EXTRACTIONS HAPPEN SIMULTANEOUSLY,
    USE THE extract_from_lead METHOD.
    """
    with reversion.create_revision():
        text, images = '', []

        # Extract either using FileDocument or WebDocument
        # as per the document type
        try:
            if lead.attachment:
                text, images = FileDocument(
                    lead.attachment.file,
                    lead.attachment.file.name,
                ).extract()

            elif lead.url:
                text, images = WebDocument(lead.url).extract()
        except Exception:
            return False

        # Save extracted text as LeadPreview
        if text:
            # Make sure there isn't existing lead preview
            LeadPreview.objects.filter(lead=lead).delete()
            # and create new one
            LeadPreview.objects.create(
                lead=lead,
                text_extract=text,
            )

        # Save extracted images as LeadPreviewImage instances
        if images:
            LeadPreviewImage.objects.filter(lead=lead).delete()
            for image in images:
                lead_image = LeadPreviewImage(lead=lead)
                lead_image.image.save(os.path.basename(image.name),
                                      File(image), True)
                lead_image.save()
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

    # Get the lead to be extracted
    lead = Lead.objects.get(id=lead_id)

    # We can't possible extract from anything other than
    # file attachment or web url
    if not lead.attachment and not lead.url:
        return False

    # Use redis store to keep track of leads currently being extracted
    # and try to prevent useless parallel extraction of same lead that
    # that might happen.
    r = redis.get_connection()
    key = 'lead_extraction_{}'.format(lead_id)
    lock = 'lock_{}'.format(key)

    # Check if key exists and if so return, otherwise set the key ourself
    # Also use lock while doing this.
    with redis.get_lock(lock):
        if r.exists(key):
            return False
        r.set(key, '1')

    # Actual extraction process
    return_value = _extract_from_lead_core(lead)

    # Send signal to all pending websocket clients
    # that the lead extraction has completed.

    code = SubscriptionConsumer.enocde({
        'channel': 'leads',
        'event': 'onPreviewExtracted',
        'leadId': lead.id,
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

    # Once done, we delete the key to say that this task is done.
    r.delete(key)
    return return_value
