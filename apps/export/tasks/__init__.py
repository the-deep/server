import logging
from celery import shared_task
from export.models import Export

from .tasks_entries import export_entries
from .tasks_assessment import export_assessments, export_planned_assessments

logger = logging.getLogger(__name__)


EXPORTER_TYPE = {
    Export.ENTRIES: export_entries,
    Export.ASSESSMENTS: export_assessments,
    Export.PLANNED_ASSESSMENTS: export_planned_assessments,
}


@shared_task
def export_task(export_id, force=False):
    try:
        export = Export.objects.get(pk=export_id)
        data_type = export.type

        # Skip if export is already started
        if not force and export.status != Export.PENDING:
            logger.warning(f'Export status is {export.get_status_display()}')
            return 'SKIPPED'

        export.status = Export.STARTED
        export.save()

        filename, export_format, mime_type, file = EXPORTER_TYPE[export.type](export)
        filename = f'Preview-{filename}' if export.is_preview else filename

        export.title = filename
        export.format = export_format
        export.mime_type = mime_type
        export.file.save(filename, file)
        export.pending = False
        export.status = Export.SUCCESS
        export.save()

        return_value = True
    except Exception:
        export = Export.objects.filter(id=export_id).first()
        if export:
            export.status = Export.FAILURE
            export.pending = False
            export.save()
        logger.error(
            'Export Failed {}!!'.format(data_type if 'data_type' in locals() else 'UNKOWN'),
            exc_info=True,
            extra={
                'data': {
                    'export_id': export_id,
                },
            },
        )
        return_value = False

    return return_value