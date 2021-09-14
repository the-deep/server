WIDGET_ID = 'numberWidget'


def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    return [{
        'filter_type': Filter.FilterType.NUMBER,
        'properties': {
            'type': 'number',
        },
    }]


def get_exportable(widget, properties):
    return {
        'excel': {
            'title': widget.title,
            'col_type': 'number',
        },
    }
