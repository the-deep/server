WIDGET_ID = 'dateRangeWidget'


def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    return [{
        'filter_type': Filter.FilterType.INTERSECTS,
        'properties': {
            'type': 'date',
        },
    }]


def get_exportable(widget, properties):
    return {
        'excel': {
            'type': 'multiple',
            'titles': [
                '{} (From)'.format(widget.title),
                '{} (To)'.format(widget.title),
            ],
            'col_type': [
                'date',
                'date',
            ],
        },
    }
