from analysis_framework.widgets.organigram_widget import WIDGET_ID

DATA_VERSION = 2


def _get_parent_nodes(node_mapping, node_key):
    node = node_mapping[node_key]
    parent_node_key = node.get("parent_node")
    parent_node = node_mapping.get(parent_node_key)

    parent_nodes = (
        [
            {
                "key": parent_node_key,
                "title": node.get("parent_title"),
            }
        ]
        if parent_node_key
        else []
    )

    if parent_node:
        parent_nodes.extend(_get_parent_nodes(node_mapping, parent_node_key))
    return parent_nodes


def _get_selected_nodes_with_parent(node, selected_ids, node_mapping=None):
    node_mapping = node_mapping or {}
    organs = node.get("children", [])

    if "key" not in node:
        return []

    if node["key"] not in node_mapping:
        node_mapping[node["key"]] = {
            "key": node["key"],
            "title": node.get("label"),
        }

    selected = []
    if node["key"] in selected_ids:
        selected.append(
            {
                "key": node["key"],
                "title": node["label"],
                "parents": _get_parent_nodes(node_mapping, node["key"]),
            }
        )

    for organ in organs:
        if "key" not in organ:
            continue

        node_mapping[organ["key"]] = {
            "key": organ["key"],
            "title": organ["label"],
            "parent_node": node["key"],
            "parent_title": node["label"],
        }
        selected.extend(
            _get_selected_nodes_with_parent(
                organ,
                selected_ids,
                node_mapping=node_mapping,
            )
        )
    return selected


def update_attribute(widget, data, widget_properties):
    values = data.get("value", [])
    base_node = widget_properties.get("options", {})

    selected_nodes_with_parents = [
        [
            *[
                # Don't show base/root as parent nodes
                parent_node["title"] if base_node.get("key") != parent_node["key"] else ""
                for parent_node in node["parents"]
            ][::-1],
            node["title"],
        ]
        for node in _get_selected_nodes_with_parent(base_node, set(values))
    ]

    return {
        "filter_data": [
            {
                "values": values,
            }
        ],
        "export_data": {
            "data": {
                "common": {
                    "widget_id": WIDGET_ID,
                    "widget_key": widget.key,
                    "version": DATA_VERSION,
                    "values": selected_nodes_with_parents,
                },
                "excel": {
                    "type": "lists",
                },
            },
        },
    }


def get_comprehensive_data(_, widget, data, widget_properties):
    values = data.get("value", [])
    return _get_selected_nodes_with_parent(widget_properties, set(values))
