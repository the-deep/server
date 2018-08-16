from analysis_framework.utils import update_widgets, Widget
from entry.utils import update_attributes, Attribute

from . import (
    matrix1d,
)


widgets = {
    'matrix1dWidget': matrix1d,
}


def migrate_widgets():
    for widget in Widget.objects.all():
        w = widgets.get(widget.widget_id)
        if not w:
            continue
        widget_data = widget.properties and \
            widget.properties.get('data')

        if not widget_data:
            continue
        widget.properties['data'] = w.migrate_widget(widget_data)
        widget.save()


def migrate_attributes():
    for attr in Attribute.objects.all():
        entry = attr.entry
        widget = attr.widget
        data = attr.data

        if not entry or not widget or not data:
            continue

        w = widgets.get(widget.widget_id)
        if not w:
            continue

        attr.data = w.migrate_attribute(attr.data)
        attr.save()


def migrate():
    migrate_widgets()
    migrate_attributes()
    update_widgets()
    update_attributes()
