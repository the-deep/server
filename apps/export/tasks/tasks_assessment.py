from celery import shared_task

from project.models import Project
from ary.models import Assessment
from export.models import Export
from export.exporters import JsonExporter
from export.assessments import ExcelExporter

import logging
logger = logging.getLogger('django')


def _export_assessments(export_type, export_id, user_id, project_id, filters):
    export = Export.objects.get(id=export_id)
    project = Project.objects.get(id=project_id)
    arys = Assessment.objects.filter(lead__project=project).distinct()
    if export_type == 'json':
        exporter = JsonExporter()
        exporter.data = {
            ary.lead.project.title: ary.to_exportable_json()
            for ary in arys
        }
        exporter.export(export)
    elif export_type == "excel":
        ExcelExporter(decoupled=False)\
            .add_assessments(arys)\
            .export(export)
    return True


@shared_task
def export_assessment(export_type, export_id, user_id, project_id, filters):
    try:
        return_value = _export_assessments(
            export_type,
            export_id,
            user_id,
            project_id,
            filters,
        )
    except Exception:
        export = Export.objects.filter(id=export_id).first()
        if export:
            export.pending = False
            export.save()
        logger.error('Export Assessment Failed', exc_info=True, extra={'export_id': export_id})
        return_value = False
    return return_value
