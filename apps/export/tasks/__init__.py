import logging
from django.utils.crypto import get_random_string

from celery import shared_task
from export.models import Export
from .tasks_entries import export_entries
from .tasks_assessment import export_assessments, export_planned_assessments

logger = logging.getLogger(__name__)


EXPORTER_TYPE = {
    Export.DataType.ENTRIES: export_entries,
    Export.DataType.ASSESSMENTS: export_assessments,
    Export.DataType.PLANNED_ASSESSMENTS: export_planned_assessments,
}


def get_export_filename(export):
    random_string = get_random_string(length=10)
    filename = f'{export.title}.{export.format}'
    if export.is_preview:
        filename = f'(Preview) {filename}'
    return f'{random_string}/{filename}'


@shared_task
def export_task(export_id, force=False):
    data_type = 'UNKNOWN'
    try:
        export = Export.objects.get(pk=export_id)
        data_type = export.type

        # Skip if export is already started
        if not force and export.status != Export.Status.PENDING:
            logger.warning(f'Export status is {export.get_status_display()}')
            return 'SKIPPED'

        export.status = Export.Status.STARTED
        export.save()

        file = EXPORTER_TYPE[export.type](export)

        export.mime_type = Export.MIME_TYPE_MAP.get(export.format, Export.DEFAULT_MIME_TYPE)
        export.file.save(get_export_filename(export), file)
        export.pending = False
        export.status = Export.Status.SUCCESS
        export.save()

        return_value = True
    except Exception:
        export = Export.objects.filter(id=export_id).first()
        if export:
            export.status = Export.Status.FAILURE
            export.pending = False
            export.save()
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
