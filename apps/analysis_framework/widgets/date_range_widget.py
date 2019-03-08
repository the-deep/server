def get_filters(widget, data):
    return [{
        'filter_type': 'intersects',
        'properties': {
            'type': 'date',
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
                'date',
                'date',
            ],
        },
    }
