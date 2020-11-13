class Dummy:
    _conditional = True


def update_attribute(widget, data, widget_data):
    from entry.widgets.store import widget_store

    value = data.get('value', {})
    selected_widget_key = value.get('selected_widget_key')

    widgets = [
        w.get('widget')
        for w in (widget_data.get('widgets') or [])
    ]

    filter_data = []
    excel_data = []
    report_data = []
    report_keys = []
    for w in widgets:
        widget_module = widget_store.get(w.get('widget_id'))
        if not widget_module:
            continue

        w_key = w.get('key')
        if w_key == selected_widget_key:
            w_data = value.get(w_key, {}).get('data', {})
        else:
            w_data = {}

        w_widget_data = w.get('properties', {}).get('data', {})

        w_obj = Dummy()
        w_obj.key = w_key
        w_obj.title = w['title']
        w_obj.widget_id = w['widget_id']

        update_info = widget_module.update_attribute(
            w_obj,
            w_data,
            w_widget_data,
        )
        w_filter_data = update_info.get('filter_data') or []
        w_export_data = update_info.get('export_data')

        filter_data = filter_data + [{
            **wfd,
            'key': '{}-{}'.format(
                widget.key,
                wfd.get('key', w_key),
            )
        } for wfd in w_filter_data]

        if w_export_data:
            excel_data.append({
                **w_export_data.get('data', {}).get('common', {}),
                **w_export_data.get('data', {}).get('excel', {}),
            })
            report_datum = {
                **w_export_data.get('data', {}).get('common', {}),
                **w_export_data.get('data', {}).get('report', {}),
            }
            report_keys += report_datum.get('keys') or []
            report_data.append(report_datum)
        else:
            excel_data.append(None)

    return {
        'filter_data': filter_data,
        'export_data': {
            'data': {
                'excel': excel_data,
                'report': {
                    'other': report_data,
                    'keys': report_keys,
                },
                # TODO: 'condition':
            },
        },
    }


def get_comprehensive_data(widgets_meta, widget, data, widget_data):
    from entry.widgets.store import widget_store

    value = data.get('value', {})
    selected_widget_key = value.get('selected_widget_key')

    selected_widgets = [
        w.get('widget')
        for w in (widget_data.get('widgets') or []) if w.get('widget', {}).get('key') == selected_widget_key
    ]

    selected_widget = selected_widgets[0] if selected_widgets else None
    if selected_widget is None:
        return None

    widget_module = widget_store.get(selected_widget.get('widget_id'))
    if widget_module is None:
        return None

    w_key = selected_widget.get('key')
    if w_key == selected_widget_key:
        w_data = value.get(w_key, {}).get('data', {})
    else:
        w_data = {}

    w_widget_data = selected_widget.get('properties', {}).get('data', {})

    w_obj = Dummy()
    w_obj.pk = f"${w_key}-{selected_widget.get('widget_id')}"
    w_obj.key = w_key

    return {
        'id': selected_widget.get('key'),
        'type': selected_widget.get('widget_id'),
        'title': selected_widget.get('title'),
        'value': widget_module.get_comprehensive_data(
            widgets_meta,
            w_obj,
            w_data,
            w_widget_data,
        )
    }
