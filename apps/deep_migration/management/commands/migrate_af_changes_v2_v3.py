import json
import copy

from django.core.management.base import BaseCommand
from analysis_framework.models import Widget, Section
from entry.models import Attribute


def clone_data(src_data, mapping):
    return {
        key: src_data.get(src_key)
        for key, src_key, _ in mapping
    }


def verifiy_data(data, src_data, mapping):
    for key, _, is_required in mapping:
        if is_required and data.get(key) in ['', None]:
            print(f'-- {key}')
            print(json.dumps(src_data, indent=2))
            print(json.dumps(data, indent=2))
            raise Exception('Data is required here')


def matrix1d_property_convertor(properties):
    """
    OLD PROPERTIES:
        rows: [
            key: string
            title: string
            tooltip: string
            color: string
            cells: [
                key: string
                value: string
                tooltip: string
            ]
        ]
    }

    NEW PROPERTIES:
        rows: [
            key: string
            label: string
            tooltip?: string
            order: number
            color: string
            cells: [
                key: string
                label: string
                tooltip?: string
                order: number
            ]
        ]
    }
    """
    if properties in [None, {}]:
        return {
            'rows': [],
        }

    ROW_MAP = [
        # dest, src keys, required
        ('key', 'key', True),
        ('label', 'title', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
        ('color', 'color', True),
    ]
    CELL_MAP = [
        # dest, src keys
        ('key', 'key', True),
        ('label', 'value', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
    ]

    new_rows = []
    row_order = 0
    for row in properties['rows']:
        new_row = clone_data(row, ROW_MAP)
        new_row['label'] = new_row['label'] or 'Untitled Row'
        new_row['color'] = new_row['color'] or '#808080'
        new_row['order'] = row_order

        new_cells = []
        cell_order = 0
        for cell in row['cells']:
            new_cell = clone_data(cell, CELL_MAP)
            new_cell['label'] = new_cell['label'] or 'Untitled Cell'
            new_cell['order'] = cell_order
            verifiy_data(new_cell, cell, CELL_MAP)
            new_cells.append(new_cell)
            cell_order += 1
        new_row['cells'] = new_cells

        verifiy_data(new_row, row, ROW_MAP)
        new_rows.append(new_row)
        row_order += 1
    # New property
    return {
        'rows': new_rows
    }


def matrix2d_property_convertor(properties):
    """
    OLD PROPERTIES:
        dimensions: [
            id: string
            title: string
            tooltip: string
            color: string
            subdimensions: [
                id: string
                title: string
                tooltip: string
            ]
        ]
        sectors: [
            id: string
            title: string
            tooltip: string
            subsectors: [
                id: string
                title: string
                tooltip: string
            ]
        ]
    }

    PROPERTIES:
        rows: [
            key: string
            label: string
            tooltip?: string
            order: number
            color: string
            subRows: [
                key: string
                label: string
                tooltip?: string
                order: number
            ]
        ]
        columns: [
            key: string
            label: string
            tooltip?: string
            order: number
            subColumns: [
                key: string
                label: string
                tooltip?: string
                order: number
            ]
        ]
    }
    """

    ROW_MAP = [
        # dest, src keys
        ('key', 'id', True),
        ('label', 'title', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
        ('color', 'color', True),
    ]
    SUB_ROW_MAP = [
        # dest, src keys
        ('key', 'id', True),
        ('label', 'title', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
    ]
    COLUMN_MAP = [
        # dest, src keys
        ('key', 'id', True),
        ('label', 'title', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
    ]
    SUB_COLUMN_MAP = [
        # dest, src keys
        ('key', 'id', True),
        ('label', 'title', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
    ]

    if properties in [None, {}]:
        return {
            'rows': [],
            'columns': [],
        }
    # rows/dimensions
    new_rows = []
    row_order = 0
    for dimension in properties['dimensions']:
        new_row = clone_data(dimension, ROW_MAP)
        new_row['order'] = row_order
        new_row['label'] = new_row['label'] or 'Untitled Row'
        new_row['color'] = new_row['color'] or '#808080'

        new_sub_rows = []
        sub_row_order = 0
        for subdimension in dimension['subdimensions']:
            new_sub_row = clone_data(subdimension, SUB_ROW_MAP)
            new_sub_row['label'] = new_sub_row['label'] or 'Untitled SubRow'
            new_sub_row['order'] = sub_row_order
            verifiy_data(new_sub_row, subdimension, SUB_ROW_MAP)
            new_sub_rows.append(new_sub_row)
            sub_row_order += 1
        new_row['subRows'] = new_sub_rows

        verifiy_data(new_row, dimension, ROW_MAP)
        new_rows.append(new_row)
        row_order += 1

    # columns/sectors
    new_columns = []
    column_order = 0
    for sector in properties['sectors']:
        new_column = clone_data(sector, COLUMN_MAP)
        new_column['order'] = column_order
        new_column['label'] = new_column['label'] or 'Untitled Column'

        new_sub_columns = []
        sub_column_order = 0
        for subsector in sector['subsectors']:
            new_sub_column = clone_data(subsector, SUB_COLUMN_MAP)
            new_sub_column['label'] = new_sub_column['label'] or 'Untitled SubRow'
            new_sub_column['order'] = sub_column_order
            verifiy_data(new_sub_column, subsector, SUB_COLUMN_MAP)
            new_sub_columns.append(new_sub_column)
            sub_column_order += 1
        new_column['subColumns'] = new_sub_columns

        verifiy_data(new_column, sector, COLUMN_MAP)
        new_columns.append(new_column)
        column_order += 1
    # New property
    return {
        'rows': new_rows,
        'columns': new_columns,
    }


def multiselect_property_convertor(properties):
    """
    OLD PROPERTIES:
        options: [
            key: string
            label: string
        ]
    PROPERTIES:
        options: [
            key: string
            label: string
            tooltip?: string
            order: number
        ]
    """
    if properties in [None, {}]:
        return {
            'options': [],
        }

    OPTION_MAP = [
        # dest, src keys
        ('key', 'key', True),
        ('label', 'label', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
    ]
    options = (
        properties if type(properties) == list
        else properties['options']
    )
    new_options = []
    option_order = 0
    for option in options:
        new_option = clone_data(option, OPTION_MAP)
        new_option['label'] = new_option['label'] or 'Untitled'
        new_option['order'] = option_order
        verifiy_data(new_option, option, OPTION_MAP)
        new_options.append(new_option)
        option_order += 1
    return {
        'options': new_options,
    }


def organigram_property_convertor(properties):
    """
    OLD PROPERTIES:
        options: [
            key: string
            title: string
        ]
    PROPERTIES:
        options:
            key: string
            label: string
            tooltip?: string
            order: number
            children: [...parent structure]
    """
    OPTION_MAP = [
        # dest, src keys
        ('key', 'key', True),
        ('label', 'title', True),
        ('tooltip', 'tooltip', False),
        ('order', 'order', True),
    ]

    def _get_all_new_options(option, order=0):
        if option == {}:
            return
        new_option = clone_data(option, OPTION_MAP)
        new_option['label'] = new_option['label'] or 'Untitled'
        new_option['order'] = order
        verifiy_data(new_option, option, OPTION_MAP)
        order += 1

        new_childerns = []
        for organ in option.pop('organs', []):
            child_organ = _get_all_new_options(organ, order=order)
            if child_organ:
                new_childerns.append(child_organ)
        new_option['children'] = new_childerns
        return new_option

    if properties in [None, []]:
        return {
            'options': [],
        }
    return {
        'options': _get_all_new_options(properties)
    }


def scale_property_convertor(properties):
    """
    OLD PROPERTIES:
        scale_units: [
            key: string
            label: string
            title: string
            color: string
            default: string
        ]
    PROPERTIES:
        options: [
            key: string
            label: string
            tooltip?: string
            order: number
            color: string
        ]
    """
    OPTION_MAP = [
        # dest, src keys
        ('key', 'key', True),
        ('label', 'label', True),
        ('tooltip', 'tooltip', False),
        ('color', 'color', True),
        ('order', 'order', True),
    ]

    if properties in [None, {}]:
        return {
            'options': [],
        }
    new_options = []
    default_option = None
    scale_order = 0
    for scale_unit in properties['scale_units'] or []:
        new_option = clone_data(scale_unit, OPTION_MAP)
        new_option['label'] = new_option['label'] or scale_unit.get('title') or 'Untitled'
        new_option['color'] = new_option['color'] or '#808080'
        new_option['order'] = scale_order

        # For default case
        if scale_unit.get('default'):
            if default_option is not None:
                print(f'- Multiple defaults found: {default_option}')
            default_option = scale_unit['key']

        verifiy_data(new_option, scale_unit, OPTION_MAP)
        new_options.append(new_option)
        scale_order += 1
    return {
        'options': new_options,
        'defaultValue': default_option,
    }


def date_range_attribute_data_convertor(data):
    value = data.get('value') or {}
    return {
        'value': {
            'startDate': value.get('from'),
            'endDate': value.get('to'),
        }
    }


def time_range_attribute_data_convertor(data):
    value = data.get('value') or {}
    return {
        'value': {
            'startTime': value.get('from'),
            'endTime': value.get('to'),
        }
    }


def geo_attribute_data_convertor(data):
    values = data.get('value') or []
    geo_ids = []
    polygons = []
    points = []
    for value in values:
        if type(value) is dict:
            value_type = value.get('type')
            if value_type == 'Point':
                points.append(value)
            else:
                polygons.append(value)
        else:
            geo_ids.append(value)
    return {
        'value': geo_ids,
        'polygons': polygons,
        'points': points,
    }


WIDGET_MIGRATION_MAP = {
    Widget.WidgetType.MATRIX1D: matrix1d_property_convertor,
    Widget.WidgetType.MATRIX2D: matrix2d_property_convertor,
    Widget.WidgetType.MULTISELECT: multiselect_property_convertor,
    Widget.WidgetType.SELECT: multiselect_property_convertor,
    Widget.WidgetType.ORGANIGRAM: organigram_property_convertor,
    Widget.WidgetType.SCALE: scale_property_convertor,
}

ATTRIBUTE_MIGRATION_MAP = {
    Widget.WidgetType.DATE_RANGE: date_range_attribute_data_convertor,
    Widget.WidgetType.TIME_RANGE: time_range_attribute_data_convertor,
    Widget.WidgetType.GEO: geo_attribute_data_convertor,
}


class Command(BaseCommand):
    CURRENT_VERSION = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.af_default_sections = {
            # AF id: default section
        }

    def get_section_for_af_id(self, af_id):
        if af_id not in self.af_default_sections:
            self.af_default_sections[af_id] = Section.objects.get_or_create(
                analysis_framework_id=af_id,
                title='Overview',
            )[0]  # NOTE: Check if multiple exists if required
        return self.af_default_sections[af_id]

    """

    for widget in Widget.objects.filter(properties__old_properties__isnull=False):
        if widget.properties.get('old_properties'):
            widget.properties = widget.properties['old_properties']
            widget.save(update_fields=('properties',))

    for attr in Attribute.objects.filter(data__old_data__isnull=False):
        if attr.data.get('old_data'):
            attr.data = attr.data['old_data']
            attr.save(update_fields=('data',))
    """

    def handle(self, *args, **kwargs):
        widget_qs = Widget.objects.exclude(version=self.CURRENT_VERSION)
        attribute_qs = Attribute.objects.exclude(widget_version=self.CURRENT_VERSION)

        # Migrate Widget Data
        print(f'Widgets (Total: {widget_qs.count()})')
        for widget_type, widget_property_convertor in WIDGET_MIGRATION_MAP.items():
            print(f'\n- {widget_type}')
            required_widgets_qs = widget_qs.filter(widget_id=widget_type)
            total = required_widgets_qs.count()
            for index, widget in enumerate(required_widgets_qs.all(), 1):
                # Update properties.
                if widget.properties.get('added_from') == 'overview':  # Requires section
                    widget.section = self.get_section_for_af_id(widget.analysis_framework_id)
                old_properties = copy.deepcopy(widget.properties.get('data') or {})
                widget.properties = widget_property_convertor(old_properties)
                # print_property(widget)
                widget.properties['old_properties'] = old_properties  # Clean-up this later.
                widget.version = self.CURRENT_VERSION
                # Save
                widget.save(update_fields=('properties', 'version', 'section'))
                print(f'-- Saved ({index})/({total})', end='\r')

        # Migrate Entry Attribute Data
        print(f'Entry Attributes (Total: {attribute_qs.count()})')
        for widget_type, attribute_data_convertor in ATTRIBUTE_MIGRATION_MAP.items():
            print(f'\n- {widget_type}')
            required_attribute_qs = attribute_qs.filter(widget__widget_id=widget_type)
            total = required_attribute_qs.count()
            for index, attribute in enumerate(required_attribute_qs.all()):
                # Update properties.
                old_data = copy.deepcopy(attribute.data or {})
                attribute.data = attribute_data_convertor(old_data)
                # print_attribute_data(attribute)
                attribute.data['old_data'] = old_data  # Clean-up this later.
                attribute.widget_version = self.CURRENT_VERSION
                # Save
                attribute.save(update_fields=('data', 'widget_version',))
                print(f'-- Saved ({index})/({total})', end='\r')
        print('')


def print_property(widget):
    import json
    print('-' * 22)
    print(json.dumps(widget.properties, indent=2))


def print_attribute_data(widget):
    import json
    print('-' * 22)
    print(json.dumps(widget.data, indent=2))
