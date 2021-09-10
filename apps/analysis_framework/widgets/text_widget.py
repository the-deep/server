WIDGET_ID = 'textWidget'


def get_filters(widget, data):
    from analysis_framework.models import Filter  # To avoid circular import

    return [{
        'filter_type': Filter.FilterType.TEXT,
        'properties': {
            'type': 'text',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
