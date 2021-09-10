WIDGET_ID = 'timeWidget'


def get_filters(widget, data):
    from analysis_framework.models import Filter  # To avoid circular import

    return [{
        'filter_type': Filter.FilterType.NUMBER,
        'properties': {
            'type': 'time',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
            'col_type': 'time',
        },
    }
