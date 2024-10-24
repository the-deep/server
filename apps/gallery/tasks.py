import reversion
import logging
from redis_store import redis
from celery import shared_task

from utils.extractor.file_document import FileDocument
from utils.common import sanitize_text
from gallery.models import (
    File,
    FilePreview,
)

logger = logging.getLogger(__name__)

# SEE lead.tasks for better explanation of these functions


def _extract_from_file_core(file_preview_id):
    file_preview = FilePreview.objects.get(id=file_preview_id)
    files = File.objects.filter(id__in=file_preview.file_ids)

    with reversion.create_revision():
        all_text = ''

        for i, file in enumerate(files):
            try:
                text, images, page_count = FileDocument(
                    file.file,
                    file.file.name,
                ).extract()

                text = sanitize_text(text)

                if i != 0:
                    all_text += '\n\n'
                all_text += text
            except Exception:
                logger.error('gallery._extract_from_file_core', exc_info=True)
                continue
        if all_text:
            file_preview.text = all_text
        file_preview.extracted = True
        file_preview.save()

    return True


@shared_task
def extract_from_file(file_preview_id):
    key = 'file_extraction_{}'.format(file_preview_id)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    try:
        return_value = _extract_from_file_core(file_preview_id)
    except Exception:
        logger.error('gallery.extract_from_file', exc_info=True)
        return_value = False

    lock.release()
    return return_value
