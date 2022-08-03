import logging
import os

from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.files.base import File
from django.conf import settings

from celery import shared_task

from deep.celery import CeleryQueue
from utils.common import makedirs
from export.models import Export
from .tasks_entries import export_entries
from .tasks_assessment import export_assessments, export_planned_assessments
from .tasks_analyses import export_analyses

logger = logging.getLogger(__name__)


EXPORTER_TYPE = {
    Export.DataType.ENTRIES: export_entries,
    Export.DataType.ASSESSMENTS: export_assessments,
    Export.DataType.PLANNED_ASSESSMENTS: export_planned_assessments,
    Export.DataType.ANALYSES: export_analyses,
}


def get_export_filename(export):
    random_string = get_random_string(length=10)
    filename = f'{export.title}.{export.format}'
    if export.is_preview:
        filename = f'(Preview) {filename}'
    return f'{random_string}/{filename}'


@shared_task(queue=CeleryQueue.EXPORT_HEAVY)
def export_task(export_id, force=False):
    data_type = 'UNKNOWN'
    try:
        export = Export.objects.get(pk=export_id)
        data_type = export.type
        # Skip if export is already started
        if not force and export.status != Export.Status.PENDING:
            logger.warning(f'Export status is {export.get_status_display()}')
            return 'SKIPPED'

        # Update status to STARTED
        export.status = Export.Status.STARTED
        export.started_at = timezone.now()
        export.save(update_fields=('status', 'started_at',))

        makedirs(settings.EXPORT_TEMP_SAVE_DIRECTORY)
        export_filename = os.path.join(
            settings.EXPORT_TEMP_SAVE_DIRECTORY,
            f'export-{export.id}.{export.format}',
        )
        # Make directory if not exists
        EXPORTER_TYPE[export.type](export, export_filename)

        with open(export_filename, 'rb') as file:
            export.mime_type = Export.MIME_TYPE_MAP.get(
                export.format,
                Export.DEFAULT_MIME_TYPE,
            )
            export.file.save(
                get_export_filename(export),
                File(file),
            )

        # Delete temp file.
        os.unlink(export_filename)

        # Update status to SUCCESS
        export.status = Export.Status.SUCCESS
        export.ended_at = timezone.now()
        export.save()

        return_value = True
    except Exception:
        export = Export.objects.filter(id=export_id).first()
        # Update status to FAILURE
        if export:
            export.status = Export.Status.FAILURE
            export.ended_at = timezone.now()
            export.save(update_fields=('status', 'ended_at',))
        logger.error(
            f'Export Failed {data_type}!!',
            exc_info=True,
            extra={
                'data': {
                    'export_id': export_id,
                },
            },
        )
        return_value = False

    return return_value
