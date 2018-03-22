from entry.models import Attribute
from .widgets.store import widget_store


def update_entry_attribute(attribute):
    entry = attribute.entry
    widget = attribute.widget
    data = attribute.data
    if not entry or not widget or not data:
        return

    widget_module = widget_store.get(widget.widget_id)
    if widget_module:
        widget_data = widget.properties and widget.properties.get('data')
        widget_module.update_attribute(entry, widget,
                                       data, widget_data or {})


def update_attributes():
    attributes = Attribute.objects.all()

    for attribute in attributes:
        update_entry_attribute(attribute)
