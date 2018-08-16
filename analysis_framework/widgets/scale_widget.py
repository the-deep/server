def get_filters(widget, data):
    scale_units = data.get('scale_units', [])
    filter_options = [
        {
            'label': s.get('label'),
            'key': s.get('key'),
        } for s in scale_units
    ]

    return [{
        'filter_type': 'list',
        'properties': {
            'type': 'multiselect-range',
            'options': filter_options
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
