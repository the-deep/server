WIDGET_ID = 'conditionalWidget'


class DummyWidget:
    def __init__(self, kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_nested_filters(original_widget, widget):
    from analysis_framework.widgets.store import widget_store
    widget_data = widget.properties and widget.properties.get('data')
    widget_module = widget_store.get(widget.widget_id)

    if hasattr(widget_module, 'get_filters'):
        filters = widget_module.get_filters(
            widget,
            widget_data or {},
        ) or []

        return [{
            **filter,
            'title': '{} - {}'.format(
                original_widget.title,
                filter.get('title', widget.title)
            ),
            'key': '{}-{}'.format(
                original_widget.key,
                filter.get('key', widget.key),
            ),
        } for filter in filters]

    return []


def get_filters(original_widget, data):
    widgets = data.get('widgets') or []
    filters = []
    for w in widgets:
        widget = DummyWidget(w.get('widget'))
        filters = filters + get_nested_filters(original_widget, widget)
    return filters


def get_nested_exportable(widget):
    from analysis_framework.widgets.store import widget_store
    widget_data = widget.properties and widget.properties.get('data')
    widget_module = widget_store.get(widget.widget_id)

    if hasattr(widget_module, 'get_exportable'):
        return widget_module.get_exportable(
            widget,
            widget_data or {},
        ) or {}
    return {}


def get_exportable(widget, data):
    widgets = data.get('widgets') or []
    exportables = []
    for w in widgets:
        widget = DummyWidget(w.get('widget'))
        exportables.append(get_nested_exportable(widget))

    return {
        'excel': {
            'type': 'nested',
            'title': widget.title,
            'children': [
                e.get('excel')
                for e in exportables
                if e.get('excel')
            ]
        },
        'report': {
            'levels': [
                level
                for e in exportables
                if e.get('report', {}).get('levels')
                for level in e['report']['levels']
            ]
        }
    }
