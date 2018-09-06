def get_filters(widget, data):
    return []


def get_exportable(widget, data):
    return {
        'excel': {
            'type': 'multiple',
            'titles': [
                '{} (From)'.format(widget.title),
                '{} (To)'.format(widget.title),
            ],
        },
    }
