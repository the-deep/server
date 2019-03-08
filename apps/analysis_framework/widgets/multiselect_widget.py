def get_filters(widget, data):
    return [{
        'filter_type': 'list',
        'properties': {
            'type': 'multiselect',
            'options': data if type(data) == list else data.get('options', []),
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
