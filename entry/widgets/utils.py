from analysis_framework.models import Filter, Exportable
from entry.models import FilterData, ExportData


def set_filter_data(entry, widget, index=0,
                    number=None, values=None):
    filter = Filter.objects.filter(
        widget_key=widget.key,
        analysis_framework=widget.analysis_framework,
    )[index]
    FilterData.objects.get_or_create(
        entry=entry,
        filter=filter,
        defaults={
            'number': number,
            'values': values,
        },
    )


def set_export_data(entry, widget, data):
    exportable = Exportable.objects.get(
        widget_key=widget.key,
        analysis_framework=widget.analysis_framework,
    )
    ExportData.objects.get_or_create(
        entry=entry,
        exportable=exportable,
        defaults={
            'data': data,
        },
    )
