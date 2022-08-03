from analysis.models import AnalyticalStatementEntry
from export.models import Export

from export.analyses.excel_exporter import ExcelExporter


def export_analyses(export, filename):
    export_type = export.export_type
    analysis = export.analysis

    analytical_statement_entries = AnalyticalStatementEntry.objects.filter(
        analytical_statement__analysis_pillar__analysis=analysis
    )

    if export_type == Export.ExportType.EXCEL:
        ExcelExporter(analytical_statement_entries)\
            .add_analytical_statement_entries(analytical_statement_entries)\
            .export(filename)
    else:
        raise Exception(
            f'(Analysis Export) Unkown Export Type Provided: {export_type} for Export: {export.id} to {filename}'
        )
