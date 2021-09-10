WIDGET_ID = 'scaleWidget'


def get_filters(widget, data):
    from analysis_framework.models import Filter  # To avoid circular import

    scale_units = data.get('scale_units', [])
    filter_options = [
        {
            'label': s.get('label'),
            'key': s.get('key'),
        } for s in scale_units
    ]

    return [{
        'filter_type': Filter.FilterType.LIST,
        'properties': {
            'type': 'multiselect-range',
            'options': filter_options
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
