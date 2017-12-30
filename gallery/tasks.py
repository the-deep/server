from celery import shared_task
from gallery.models import (
    File,
    FilePreview,
)
from lead.tasks import _preprocess
from utils.extractor.file_document import FileDocument

from redis_store import redis
import reversion

import traceback
import logging

logger = logging.getLogger(__name__)


# SEE lead.tasks for better explanation of these functions
# This is a simpler version of that module with lots of unnecessary
# stuffs removed and using File instead of Lead


def _extract_from_file_core(file_id):
    file = File.objects.get(id=file_id)

    with reversion.create_revision():
        text, images = '', []

        try:
            text, images = FileDocument(
                file.file,
                file.file.name,
            ).extract()

            text = _preprocess(text)
        except Exception as e:
            logger.error(traceback.format_exc())
            return False

        if text:
            FilePreview.objects.create(
                file=file,
                text_extract=text,
            )

    return True


@shared_task
def extract_from_file(file_id):
    r = redis.get_connection()
    key = 'file_extraction_{}'.format(file_id)
    lock = 'lock_{}'.format(key)

    with redis.get_lock(lock):
        if r.exists(key):
            return False
        r.set(key, '1')

    try:
        return_value = _extract_from_file_core(file_id)
    except Exception as e:
        logger.error(traceback.format_exc())
        return_value = False

    r.delete(key)
    return return_value
