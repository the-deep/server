def get_selected_nodes(node, selected_ids):
    selected = []
    organs = node.get('organs', [])
    for organ in organs:
        selected.extend(get_selected_nodes(organ, selected_ids))

    if node.get('key') in selected_ids:
        selected.append(node)
    return selected


def update_attribute(widget, data, widget_data):
    values = data.get('value', [])
    selected_nodes = get_selected_nodes(widget_data, values)

    return {
        'filter_data': [{
            'values': values,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'type': 'list',
                    'value': [v.get('name') for v in selected_nodes],
                },
            },
        },
    }
