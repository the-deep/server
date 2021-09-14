WIDGET_ID = 'selectWidget'

"""
properties:
    options: [
        clientId: string  # TODO: Change this to key or any other name
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
