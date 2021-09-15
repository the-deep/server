from analysis_framework.models import Widget, Filter, Exportable
from .widgets.store import widget_store


def update_widget(widget):
    widget_properties = widget.properties or {}
    widget_module = widget_store.get(widget.widget_id)

    if widget_module is None:
        raise Exception(f'Unknown widget type: {widget.widet_id}')

    if hasattr(widget_module, 'get_filters'):
        filters = widget_module.get_filters(widget, widget_properties) or []
        for filter in filters:
            filter['title'] = filter.get('title', widget.title)
            Filter.objects.update_or_create(
                analysis_framework=widget.analysis_framework,
                widget_key=widget.key,
                key=filter.get('key', widget.key),
                defaults=filter,
            )

    if hasattr(widget_module, 'get_exportable'):
        exportable = widget_module.get_exportable(widget, widget_properties)
        if exportable:
            Exportable.objects.update_or_create(
                analysis_framework=widget.analysis_framework,
                widget_key=widget.key,
                defaults={
                    'data': exportable,
                },
            )


def update_widgets(widget_id=None, **widget_filters):
    if widget_id:
        widgets = Widget.objects.filter(widget_id=widget_id)
    else:
        widgets = Widget.objects.filter(**widget_filters)

    for widget in widgets:
        update_widget(widget)
