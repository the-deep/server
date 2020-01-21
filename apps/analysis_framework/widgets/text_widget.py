def get_filters(widget, data):
    return [{
        'filter_type': 'text',
        'properties': {
            'type': 'text',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
