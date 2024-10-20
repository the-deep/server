WIDGET_ID = 'organigramWidget'

"""
properties:
    options:
        key: string
        label: string
        tooltip?: string
        order: number
        children: [...parent structure]
"""


def get_values_for_organ(organ, parent_label=None):
    label = organ.get('label', '')
    if parent_label:
        label = '{} / {}'.format(parent_label, label)

    values = [{
        'key': organ.get('key'),
        'label': label,
    }]

    for organ in organ.get('children') or []:
        values.extend(
            get_values_for_organ(organ, label)
        )

    return values


def get_filters(widget, properties):
    from analysis_framework.models import Filter  # To avoid circular import

    options = []
    raw_options = properties and properties.get('options')
    if raw_options:
        options = get_values_for_organ(raw_options, None)
    return [{
        'filter_type': Filter.FilterType.LIST,
        'properties': {
            'type': 'multiselect',
            'options': options,
        },
    }]


def get_exportable(widget, properties):
    def _get_depth(organ, level=1):
        child_organs = organ.get('children') or []
        if len(child_organs) == 0:
            return level
        depths = []
        for c_organ in child_organs:
            depths.append(
                _get_depth(c_organ, level=level + 1)
            )
        return max(depths)

    options = (properties and properties.get('options')) or {}
    return {
        'excel': {
            'type': 'multiple',
            'titles': [
                f'{widget.title} - Level {level}'
                for level in range(
                    _get_depth(options)
                )
            ],
        },
    }
