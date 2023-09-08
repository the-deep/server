import logging
from django.utils import timezone

from celery import shared_task

from deep.celery import CeleryQueue
from export.models import Export, GenericExport
from .tasks_entries import export_entries
from .tasks_assessment import export_assessments
from .tasks_analyses import export_analyses
from .tasks_projects import export_projects_stats

logger = logging.getLogger(__name__)


EXPORTER_TYPE = {
    Export.DataType.ENTRIES: export_entries,
    Export.DataType.ASSESSMENTS: export_assessments,
    Export.DataType.ANALYSES: export_analyses,
}
GENERIC_EXPORTER_TYPE = {
    GenericExport.DataType.PROJECTS_STATS: export_projects_stats,
}


def get_export_filename(export):
    filename = f'{export.title}.{export.format}'
    if getattr(export, 'is_preview', False):
        filename = f'(Preview) {filename}'
    return filename


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

        file = EXPORTER_TYPE[export.type](export)

        export.mime_type = Export.MIME_TYPE_MAP.get(export.format, Export.DEFAULT_MIME_TYPE)
        export.file.save(get_export_filename(export), file)

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


# NOTE: limit are in seconds
@shared_task(queue=CeleryQueue.DEFAULT, time_limit=220, soft_time_limit=120)
def generic_export_task(export_id, force=False):
    data_type = 'UNKNOWN'
    try:
        export = GenericExport.objects.get(pk=export_id)
        data_type = export.type
        # Skip if export is already started
        if not force and export.status != GenericExport.Status.PENDING:
            logger.warning(f'Generic Export status is {export.get_status_display()}')
            return 'SKIPPED'

        # Update status to STARTED
        export.status = GenericExport.Status.STARTED
        export.started_at = timezone.now()
        export.save(update_fields=('status', 'started_at',))

        file = GENERIC_EXPORTER_TYPE[export.type](export)

        export.mime_type = GenericExport.MIME_TYPE_MAP.get(export.format, GenericExport.DEFAULT_MIME_TYPE)
        export.file.save(get_export_filename(export), file)

        # Update status to SUCCESS
        export.status = GenericExport.Status.SUCCESS
        export.ended_at = timezone.now()
        export.save()

        return_value = True
    except Exception:
        export = GenericExport.objects.filter(id=export_id).first()
        # Update status to FAILURE
        if export:
            export.status = GenericExport.Status.FAILURE
            export.ended_at = timezone.now()
            export.save(update_fields=('status', 'ended_at',))
        logger.error(
            f'Generic Export Failed {data_type}!!',
            exc_info=True,
            extra={
                'data': {
                    'export_id': export_id,
                },
            },
        )
        return_value = False

    return return_value
