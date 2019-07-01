def _get_parent_nodes(node_mapping, node_key):
    parent_node_key = node_mapping[node_key].get('parent_node')
    parent_node = node_mapping.get(parent_node_key)
    parent_nodes = [{
        'key': parent_node_key,
        'title': node_mapping[node_key]['parent_title'],
    }]
    if parent_node:
        parent_nodes.extend(
            _get_parent_nodes(node_mapping, parent_node_key)
        )
    return parent_nodes


def _get_selected_nodes_with_parent(node, selected_ids, node_mapping=None):
    node_mapping = node_mapping or {}
    selected = []
    organs = node.get('organs', [])

    if node['key'] in selected_ids:
        selected.append({
            'key': node['key'],
            'title': node['title'],
            'parents': _get_parent_nodes(node_mapping, node['key']),
        })

    for organ in organs:
        node_mapping[organ['key']] = {
            'key': organ['key'],
            'title': organ['title'],
            'parent_node': node['key'],
            'parent_title': node['title'],
        }
        selected.extend(
            _get_selected_nodes_with_parent(
                organ, selected_ids, node_mapping,
            )
        )
    return selected


def _get_selected_nodes(node, selected_ids):
    selected = []
    organs = node.get('organs', [])
    for organ in organs:
        selected.extend(_get_selected_nodes(organ, selected_ids))

    if node.get('key') in selected_ids:
        selected.append(node)
    return selected


def update_attribute(widget, data, widget_data):
    values = data.get('value', [])
    selected_nodes = _get_selected_nodes(widget_data, values)

    return {
        'filter_data': [{
            'values': values,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'type': 'list',
                    # TODO: Add migration for this fix
                    'value': [v.get('title') for v in selected_nodes],
                },
            },
        },
    }


def get_comprehensive_data(_, widget, data, widget_data):
    values = data.get('value', [])
    return _get_selected_nodes_with_parent(widget_data, values)
