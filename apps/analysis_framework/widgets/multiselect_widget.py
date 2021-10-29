WIDGET_ID = 'multiselectWidget'

"""
properties:
    options: [
        key: string
        label: string
        tooltip?: string
        order: number
    ]
"""


def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    return [{
        'filter_type': Filter.FilterType.LIST,
        'properties': {
            'type': 'multiselect',
            'options': properties.get('options', []),
        },
    }]


def get_exportable(widget, properties):
    return {
        'excel': {
            'title': widget.title,
        },
    }
