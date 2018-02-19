def get_filters(widget, data):
    return [{
        'filter_type': 'number',
        'properties': {
            'type': 'date',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
