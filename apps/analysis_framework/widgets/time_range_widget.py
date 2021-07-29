WIDGET_ID = 'timeRangeWidget'


def get_filters(widget, data):
    return [{
        'filter_type': 'intersects',
        'properties': {
            'type': 'time',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'type': 'multiple',
            'titles': [
                '{} (From)'.format(widget.title),
                '{} (To)'.format(widget.title),
            ],
            'col_type': [
                'time',
                'time',
            ],
        },
    }
