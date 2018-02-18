from .utils import set_filter_data, set_export_data


def get_selected_nodes(node, activeKeys):
    selected = []
    organs = node.get('organs', [])
    for organ in organs:
        selected.extend(get_selected_nodes(organ, activeKeys))

    key = node.get('key')
    if len(selected) > 0 or key in activeKeys:
        selected.append(key)

    return selected


def update_attribute(entry, widget, data, widget_data):
    values = data.get('values', [])
    selected_ids = [v.get('id') for v in values]
    selected_node_keys = get_selected_nodes(widget_data, selected_ids)

    set_filter_data(
        entry,
        widget,
        values=selected_node_keys,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'type': 'list',
                'value': [v.get('name') for v in values],
            },
        },
    )
