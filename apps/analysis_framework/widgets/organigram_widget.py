def get_values_for_organ(organ, parent_label=None):
    label = organ.get('title', '')
    if parent_label:
        label = '{} / {}'.format(parent_label, label)

    values = [{
        'key': organ.get('key'),
        'label': label,
    }]

    for organ in organ.get('organs'):
        values.extend(get_values_for_organ(organ, label))

    return values


def get_filters(widget, data):
    return [{
        'filter_type': 'list',
        'properties': {
            'type': 'multiselect',
            'options': get_values_for_organ(data, None) if data else [],
        },
    }]


def get_exportable(widget, data):
    return {
        'excel': {
            'title': widget.title,
        },
    }
