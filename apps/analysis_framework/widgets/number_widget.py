WIDGET_ID = 'numberWidget'


def get_filters(widget, data):
    return [{
        'filter_type': 'number',
        'properties': {
            'type': 'number',
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
            'col_type': 'number',
        },
    }
