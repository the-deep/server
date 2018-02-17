from .widgets.store import widget_store


def update_entry_attribute(attribute):
    entry = attribute.entry
    widget = attribute.widget
    data = attribute.data
    if not entry or not widget or not data:
        return

    widget_module = widget_store[widget.widget_id]
    if widget_module:
        widget_module.update_attribute(entry, widget, data)
