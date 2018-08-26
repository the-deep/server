def get_filters(widget, data):
    return [{
        'filter_type': 'number',
        'properties': {
            'type': 'time',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
