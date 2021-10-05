WIDGET_ID = 'scaleWidget'


"""
properties:
    options: [
        key: string
        label: string
        tooltip?: string
        order: number
        color: string
    ]
"""


def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    options = properties.get('options', [])
    filter_options = [
        {
            'label': option.get('label'),
            'key': option.get('key'),
        } for option in options
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
