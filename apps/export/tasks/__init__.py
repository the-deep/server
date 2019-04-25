import logging
from celery import shared_task
from export.models import Export

from .tasks_entries import export_entries
from .tasks_assessment import export_assessments

logger = logging.getLogger(__name__)


@shared_task
def export_task(export_id):
    try:
        export = Export.objects.get(pk=export_id)
        data_type = export.type
        if data_type == Export.ENTRIES:
            return_value = export_entries(export)
        elif data_type == Export.ASSESSMENTS:
            return_value = export_assessments(export)
    except Exception:
        export = Export.objects.filter(id=export_id).first()
        if export:
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
