WIDGET_ID = 'organigramWidget'
DATA_VERSION = 1


def _get_parent_nodes(node_mapping, node_key):
    node = node_mapping[node_key]
    parent_node_key = node.get('parent_node')
    parent_node = node_mapping.get(parent_node_key)

    parent_nodes = [{
        'key': parent_node_key,
        'title': node.get('parent_title'),
    }] if parent_node_key else []

    if parent_node:
        parent_nodes.extend(
            _get_parent_nodes(node_mapping, parent_node_key)
        )
    return parent_nodes


def _get_selected_nodes_with_parent(node, selected_ids, node_mapping=None):
    node_mapping = node_mapping or {}
    organs = node.get('organs', [])

    if 'key' not in node:
        return []

    if node['key'] not in node_mapping:
        node_mapping[node['key']] = {
            'key': node['key'],
            'title': node.get('title'),
        }

    selected = []
    if node['key'] in selected_ids:
        selected.append({
            'key': node['key'],
            'title': node['title'],
            'parents': _get_parent_nodes(node_mapping, node['key']),
        })

    for organ in organs:
        if 'key' not in organ:
            continue

        node_mapping[organ['key']] = {
            'key': organ['key'],
            'title': organ['title'],
            'parent_node': node['key'],
            'parent_title': node['title'],
        }
        selected.extend(
            _get_selected_nodes_with_parent(
                organ, selected_ids, node_mapping=node_mapping,
            )
        )
    return selected


def update_attribute(widget, data, widget_data):
    values = data.get('value', [])
    base_node = widget_data.get('key')

    selected_nodes_with_parents = [
        [
            *[
                # Don't show base/root as parent nodes
                parent_node['title'] if base_node != parent_node['key'] else ''
                for parent_node in node['parents']
            ][::-1],
            node['title'],
        ]
        for node in _get_selected_nodes_with_parent(widget_data, set(values))
    ]

    return {
        'filter_data': [{
            'values': values,
        }],

        'export_data': {
            'data': {
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                    'version': DATA_VERSION,
                },
                'excel': {
                    'type': 'lists',
                    'values': selected_nodes_with_parents,
                },
            },
        },
    }


def get_comprehensive_data(_, widget, data, widget_data):
    values = data.get('value', [])
    return _get_selected_nodes_with_parent(widget_data, set(values))
