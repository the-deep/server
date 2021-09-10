WIDGET_ID = 'geoWidget'


def get_filters(widget, data):
    from analysis_framework.models import Filter  # To avoid circular import
    return [{
        'filter_type': Filter.FilterType.LIST,
        'properties': {
            'type': 'geo',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'type': 'geo',
            'title': widget.title,
        },
    }
