from .utils import set_filter_data, set_export_data


def get_selected_nodes(node, selected_ids):
    selected = []
    organs = node.get('organs', [])
    for organ in organs:
        selected.extend(get_selected_nodes(organ, selected_ids))

    if node.get('key') in selected_ids:
        selected.append(node)
    return selected


def update_attribute(entry, widget, data, widget_data):
    values = data.get('values', [])
    selected_nodes = get_selected_nodes(widget_data, values)

    set_filter_data(
        entry,
        widget,
        values=values,
    )

    set_export_data(
        entry,
        widget,
        {
            'excel': {
                'type': 'list',
                'value': [v.get('name') for v in selected_nodes],
            },
        },
    )
