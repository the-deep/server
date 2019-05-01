import logging
from celery import shared_task
from export.models import Export

from .tasks_entries import export_entries
from .tasks_assessment import export_assessments

logger = logging.getLogger(__name__)


EXPORTER_TYPE = {
    Export.ENTRIES: export_entries,
    Export.ASSESSMENTS: export_assessments,
}


@shared_task
def export_task(export_id):
    try:
        export = Export.objects.get(pk=export_id)
        data_type = export.type

        export.status = Export.STARTED
        export.save()

        filename, export_format, mime_type, file = EXPORTER_TYPE[export.type](export)

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
