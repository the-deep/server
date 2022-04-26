import json

from django.contrib.gis.db.models import Extent
from django.utils import timezone
from django.db.models import Prefetch

from geo.models import GeoArea
from analysis_framework.models import Widget, Filter
from apps.entry.widgets.geo_widget import get_valid_geo_ids

from .models import Entry, Attribute

SUPPORTED_WIDGETS = [
    'matrix1dWidget', 'matrix2dWidget', 'scaleWidget', 'multiselectWidget', 'organigramWidget', 'geoWidget',
    'conditionalWidget',
]


def _get_lead_data(lead):
    return {
        'id': lead.id,
        'title': lead.title,
        'source_type': lead.source_type,
        'confidentiality': lead.confidentiality,
        'source_raw': lead.source_raw,
        'source': lead.source and {
            'id': lead.source.id,
            'title': lead.source.data.title,
        },
        'author_raw': lead.author_raw,
        'authors': [
            {
                'id': author.id,
                'title': author.data.title,
                # TODO: Legacy: Remove `or` logic after all the author are migrated to authors from author
            } for author in lead.authors.all() or ([lead.author] if lead.author else [])
        ],
    }


def _get_project_geoareas(project):
    qs = GeoArea.objects.filter(
        admin_level__region__in=project.regions.values_list('id'),
        admin_level__level__in=[0, 1, 2],
    ).annotate(extent=Extent('polygons')).values('pk', 'admin_level__level', 'title', 'polygons', 'extent', 'parent')
    geo_array = []

    for geoarea in qs:
        polygons = geoarea['polygons']
        centroid = polygons.centroid
        geo = {
            'id': geoarea['pk'],
            'admin_level': geoarea['admin_level__level'],
            'parent': geoarea['parent'],
            'name': geoarea['title'],
            'centroid': [centroid.x, centroid.y],
            'bounds': [geoarea['extent'][:2], geoarea['extent'][2:]],
        }
        geo['polygons'] = json.loads(polygons.geojson)   # TODO:
        geo_array.append(geo)
    return geo_array


def _get_widget_info(config, widgets, skip_data=False, default=None):
    if not config and default is not None:
        return default

    widget = widgets[config['pk']]

    def _return(properties):
        return {
            '_widget': widget,
            'pk': widget.pk,
            'config': config,
            'properties': properties,
        }

    if skip_data:
        return _return(None)

    if widget.widget_id == 'organigramWidget':
        w_filter = Filter.objects.filter(
            widget_key=widget.key,
            analysis_framework_id=widget.analysis_framework_id,
        ).first()
        return _return(w_filter.properties if w_filter else None)

    properties = widget.properties
    if config.get('is_conditional_widget'):
        # TODO: Skipping conditional widget, in new this is not needed
        return default
    return _return(properties)


def _get_attribute_widget_value(cd_widget_map, w_value, widget_type, widget_pk=None):
    if widget_type in ['scaleWidget', 'multiselectWidget', 'organigramWidget']:
        return w_value
    elif widget_type == 'geoWidget':
        # XXX: We don't need this now, as only string are stored here. Remove later.
        return get_valid_geo_ids(w_value)
    elif widget_type == 'conditionalWidget':
        cd_config = cd_widget_map.get(widget_pk)
        if cd_config is None:
            return
        selected_widget_key = cd_config['widget_key']
        selected_widget_type = cd_config['widget_type']
        selected_widget_pk = cd_config.get('widget_pk')
        return _get_attribute_widget_value(
            cd_widget_map,
            w_value[selected_widget_key]['data']['value'],
            selected_widget_type,
            selected_widget_pk,
        ) if w_value.get(selected_widget_key) else None
    elif widget_type in ['matrix1dWidget', 'matrix2dWidget']:
        context_keys = [
            f'{widget_pk}-{_value}'
            for _value in (
                w_value.keys() if isinstance(w_value, dict) else []
            )
        ]
        sectors_keys = []
        if widget_type == 'matrix2dWidget':  # Collect sector data from here
            sectors_keys = [
                [f'{widget_pk}-{pillar_key}', subpillar_key, sector_key]
                for pillar_key, pillar in w_value.items()
                for subpillar_key, subpillar in pillar.items()
                for sector_key in subpillar.keys()
            ]
        return {
            'context_keys': context_keys,
            'sectors_keys': sectors_keys,
        }


def _get_attribute_data(collector, attribute, cd_widget_map):
    widget_type = attribute.widget.widget_id
    widget_pk = attribute.widget.pk
    data = attribute.data

    if widget_type not in SUPPORTED_WIDGETS or not data or not data.get('value'):
        return

    collector[widget_pk] = _get_attribute_widget_value(cd_widget_map, data['value'], widget_type, widget_pk)


def get_project_entries_stats(project, skip_geo_data=False):
    """
    NOTE: This is a custom API made for Entries VIz and only works for certain AF.

    # Sample config
    default_config = {
        'widget_1d': [{
            'pk': 2679,
        }],
        'widget_2d': [{
            'pk': 2676,
        }],
        'geo_widget': {
            'pk': 2677,
        },
        'severity_widget': {
            'pk': 2902,
            'is_conditional_widget': True,
            'widget_key': 'scalewidget-ljlk28coxz7sufml',
            # TODO: Add validation here
            'widget_type': 'scaleWidget',
            'widget_pk': None,  # Required if widget_type is matrix
        },
        'reliability_widget': {
            'pk': 2683,
        },
        'affected_groups_widget': {
            'pk': 2682,
        },
        'specific_needs_groups_widget': {
            'pk': 2681,
        },
        'demographic_groups_widget': {
            'pk': 8703,
        },
    }
    """

    af = project.analysis_framework
    config = af.properties.get('stats_config')

    widgets_pk = [
        info['pk']
        for _info in config.values()
        for info in (_info if isinstance(_info, list) else [_info])
    ]
    cd_widget_map = {
        w_config['pk']: w_config
        for _w_config in config.values()
        for w_config in (_w_config if isinstance(_w_config, list) else [_w_config])
        if w_config.get('is_conditional_widget')
    }
    widgets = {
        widget.pk: widget
        for widget in Widget.objects.filter(pk__in=widgets_pk, analysis_framework=af)
    }

    # TODO: Remove this later after all data are updated.
    config['widget1d'] = config.get('widget1d') or config['widget_1d']
    config['widget2d'] = config.get('widget2d') or config['widget_2d']

    # Make sure this are array
    for key in ['widget1d', 'widget2d']:
        if type(config[key]) is not list:
            config[key] = [config[key]]

    w_reliability_default = w_severity_default = w_specific_needs_groups_default = w_demographic_groups_default = {
        'pk': None,
        'properties': {
            'options': [],
        },
    }

    w1ds = [_get_widget_info(_config, widgets) for _config in config['widget1d']]
    w2ds = [_get_widget_info(_config, widgets) for _config in config['widget2d']]

    w_specific_needs_groups = _get_widget_info(
        config.get('specific_needs_groups_widget'), widgets, default=w_specific_needs_groups_default
    )
    w_demographic_groups = _get_widget_info(
        config.get('demographic_groups_widget'), widgets, default=w_demographic_groups_default
    )
    w_severity = _get_widget_info(config.get('severity_widget'), widgets, default=w_severity_default)
    w_reliability = _get_widget_info(config.get('reliability_widget'), widgets, default=w_reliability_default)

    w_ag = _get_widget_info(config['affected_groups_widget'], widgets)
    w_geo = _get_widget_info(config['geo_widget'], widgets, skip_data=True)

    matrix_widgets = [
        {'id': w['pk'], 'type': w_type, 'title': w['_widget'].title}
        for widgets, w_type in [[w1ds, 'widget1d'], [w2ds, 'widget2d']]
        for w in widgets
    ]

    context_array = [
        {
            'id': f"{w['pk']}-{dimension[id_key]}",
            'widget_id': w['pk'],
            'name': dimension['label'],
            'color': dimension.get('color'),
        } for id_key, w, dimensions in [
            *[('key', w1d, w1d['properties']['rows']) for w1d in w1ds],
            *[('key', w2d, w2d['properties']['rows']) for w2d in w2ds],
        ] for dimension in dimensions
    ]
    framework_groups_array = [
        {
            'id': subdimension['key'],
            'widget_id': w2d['pk'],
            'context_id': f"{w2d['pk']}-{dimension['key']}",
            'name': subdimension['label'],
            'tooltip': subdimension.get('tooltip'),
        }
        for w2d in w2ds
        for dimension in w2d['properties']['rows']
        for subdimension in dimension['subRows']
    ]

    sector_array = [
        {
            'id': sector['key'],
            'widget_id': w2d['pk'],
            'name': sector['label'],
            'tooltip': sector.get('tooltip'),
        }
        for w2d in w2ds
        for sector in w2d['properties']['columns']
    ]
    affected_groups_array = [
        {
            'id': option['key'],
            'name': option['label'],
        } for option in w_ag['properties']['options']
    ]
    specific_needs_groups_array = [
        {
            'id': option['key'],
            'name': option['label'],
        } for option in w_specific_needs_groups['properties']['options']
    ]
    w_demographic_groups_array = [
        {
            'id': option['key'],
            'name': option['label'],
        } for option in w_demographic_groups['properties']['options']
    ]

    severity_units = [
        {
            'id': severity['key'],
            'color': severity.get('color'),
            'name': severity['label'],
        } for severity in w_severity['properties']['options']
    ]
    reliability_units = [
        {
            'id': reliability['key'],
            'color': reliability.get('color'),
            'name': reliability['label'],
        } for reliability in w_reliability['properties']['options']
    ]

    meta = {
        'data_calculated': timezone.now(),
        'matrix_widgets': matrix_widgets,
        'context_array': context_array,
        'framework_groups_array': framework_groups_array,
        'sector_array': sector_array,
        'affected_groups_array': affected_groups_array,
        'specific_needs_groups_array': specific_needs_groups_array,
        'demographic_groups_array': w_demographic_groups_array,
        'severity_units': severity_units,
        'reliability_units': reliability_units,
    }

    if not skip_geo_data:
        meta['geo_array'] = _get_project_geoareas(project)

    data = []
    entries = Entry.objects.filter(project=project).prefetch_related(
        Prefetch(
            'attribute_set',
            queryset=Attribute.objects.filter(widget_id__in=widgets_pk),
        ),
        'attribute_set__widget',
        'lead',
    )
    for entry in entries.all():
        collector = {}
        for attribute in entry.attribute_set.all():
            _get_attribute_data(collector, attribute, cd_widget_map)

        data.append({
            'pk': entry.pk,
            'created_date': entry.created_at,
            'lead': _get_lead_data(entry.lead),
            'date': entry.lead.published_on,
            'severity': collector.get(w_severity['pk']),
            'reliability': collector.get(w_reliability['pk']),
            'geo': collector.get(w_geo['pk'], []),
            'special_needs': collector.get(w_specific_needs_groups['pk'], []),
            'demographic_groups': collector.get(w_demographic_groups['pk'], []),
            'affected_groups': collector.get(w_ag['pk'], []),
            'context_sector': {
                w['pk']: {
                    'context': collector.get(w['pk'], {}).get('context_keys', []),
                    'sector': collector.get(w['pk'], {}).get('sectors_keys', []),
                }
                for w in [*w1ds, *w2ds]
            },
        })

    return {
        'meta': meta,
        'data': data,
    }
