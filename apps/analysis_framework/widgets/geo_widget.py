def get_filters(widget, data):
    return [{
        'filter_type': 'list',
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
