import json
import reversion

from analysis_framework.utils import update_widgets, Widget
from entry.utils import update_attributes, Attribute

from .projects import migrate_projects
from .ary import migrate_ary
from . import (
    matrix1d,
    matrix2d,
    scale,
    excerpt,
    organigram,
    geo,
    number_matrix,
)


widgets = {
    'matrix1dWidget': matrix1d,
    'matrix2dWidget': matrix2d,
    'scaleWidget': scale,
    'excerptWidget': excerpt,
    'organigramWidget': organigram,
    'geoWidget': geo,
    'numberMatrixWidget': number_matrix,
}

default_added_from = {
    'matrix1dWidget': 'overview',
    'matrix2dWidget': 'overview',
    'numberMatrixWidget': 'overview',
    'excerptWidget': 'overview',
    # if not specified here, default is assumed to be list
}


def migrate_widgets(**kwargs):
    for widget in Widget.objects.filter(**kwargs):
        if not widget.properties:
            widget.properties = {}

        if not widget.properties.get('added_from'):
            widget.properties['added_from'] = \
                default_added_from.get(widget.widget_id, 'list')

        widget_data = widget.properties.get('data')
        w = widgets.get(widget.widget_id)

        if widget_data and w:
            widget.properties['data'] = w.migrate_widget(widget_data)
        widget.save()


def migrate_attributes(**kwargs):
    for attr in Attribute.objects.filter(**kwargs):
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


def migrate(*args, **kwargs):
    if not kwargs.get('filters_file'):
        project_filters = {}
        widget_filters = {}
        attributes_filters = {}
        ary_filters = {}
    else:
        with open(kwargs['filters_file']) as f:
            filter_data = json.load(f)
            project_filters = filter_data.get('project_filters', {})
            widget_filters = filter_data.get('widget_filters', {})
            attributes_filters = filter_data.get('attributes_filters', {})
            ary_filters = filter_data.get('ary_filters', {})

    with reversion.create_revision():
        migrate_projects(**project_filters)
        migrate_widgets(**widget_filters)
        migrate_attributes(**attributes_filters)
        update_widgets(**widget_filters)
        update_attributes(**attributes_filters)
        migrate_ary(**ary_filters)
