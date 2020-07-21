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
    def _get_depth(organ, level=1):
        child_organs = organ.get('organs') or []
        if len(child_organs) == 0:
            return level
        depths = []
        for c_organ in child_organs:
            depths.append(_get_depth(c_organ, level=level + 1))
        return max(depths)

    return {
        'excel': {
            'type': 'multiple',
            'titles': [
                f'{widget.title} - Level {level}'
                for level in range(_get_depth(data))
            ],
        },
    }
