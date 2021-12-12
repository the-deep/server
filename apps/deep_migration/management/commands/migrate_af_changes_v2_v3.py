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


# -- Widget convertors
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


# -- Attributes convertor
MAXTIX_DATA_EMPTY_VALUES = [{}, None]


def matrix1d_attribute_data_convertor(data):
    value = data.get('value') or {}
    new_value = {}
    for row_key, row_data in value.items():
        new_row_data = {}
        for cell_key, is_selected in (row_data or {}).items():
            if is_selected:
                new_row_data[cell_key] = True
        if new_row_data not in MAXTIX_DATA_EMPTY_VALUES:
            new_value[row_key] = new_row_data
    return {
        'value': new_value
    }


def matrix2d_attribute_data_convertor(data):
    value = data.get('value') or {}
    new_value = {}
    for row_key, row_data in value.items():
        new_row_data = {}
        for sub_row_key, sub_row_data in (row_data or {}).items():
            new_sub_row_data = {}
            for column_key, sub_column_values in (sub_row_data or {}).items():
                if sub_column_values is not None:
                    new_sub_row_data[column_key] = sub_column_values
            if new_sub_row_data not in MAXTIX_DATA_EMPTY_VALUES:
                new_row_data[sub_row_key] = new_sub_row_data
        if new_row_data not in MAXTIX_DATA_EMPTY_VALUES:
            new_value[row_key] = new_row_data
    return {
        'value': new_value
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
    Widget.WidgetType.MATRIX1D: matrix1d_attribute_data_convertor,
    Widget.WidgetType.MATRIX2D: matrix2d_attribute_data_convertor,
    Widget.WidgetType.DATE_RANGE: date_range_attribute_data_convertor,
    Widget.WidgetType.TIME_RANGE: time_range_attribute_data_convertor,
    Widget.WidgetType.GEO: geo_attribute_data_convertor,
}

CONDITIONAL_OPERATOR_MAP = {
    ('matrix1dWidget', 'containsPillar'): 'matrix1d-rows-selected',
    ('matrix1dWidget', 'containsSubpillar'): 'matrix1d-cells-selected',
    ('matrix2dWidget', 'containsDimension'): 'matrix2d-rows-selected',
    ('matrix2dWidget', 'containsSubdimension'): 'matrix2d-sub-rows-selected',
    ('multiselectWidget', 'isSelected'): 'multi-selection-selected',
    ('scaleWidget', 'isEqualTo'): 'scale-selected',
    ('selectWidget', 'isSelected'): 'single-selection-selected',
}


def get_widgets_from_conditional(conditional_widget):
    af_widget_qs = Widget.objects.filter(analysis_framework_id=conditional_widget.analysis_framework_id)
    widgets = conditional_widget.properties.get('data', {}).get('widgets', [])
    for conditional_widget_data in widgets:
        widget_data = conditional_widget_data['widget']

        legacy_conditions = conditional_widget_data['conditions']
        if len(legacy_conditions['list']) == 0:
            continue
        if len(legacy_conditions['list']) > 1:
            raise Exception('Found multiple list. Not supported')
        legacy_condition = legacy_conditions['list'][0]

        parent_widget_key = legacy_condition['widget_key']
        parent_widget = af_widget_qs.get(key=parent_widget_key)
        operator = CONDITIONAL_OPERATOR_MAP[(legacy_condition['widget_id'], legacy_condition['condition_type'])]
        condition_attributes = legacy_condition.get('attributes') or {}
        invert = legacy_condition.get('invert_logic')

        if operator == 'matrix1d-rows-selected':
            condition_collection = condition_attributes.get('pillars') or {}
        elif operator == 'matrix1d-cells-selected':
            condition_collection = condition_attributes.get('subpillars') or {}
        elif operator == 'matrix2d-rows-selected':
            condition_collection = condition_attributes.get('dimensions') or {}
        elif operator == 'matrix2d-sub-rows-selected':
            condition_collection = condition_attributes.get('subdimensions') or {}
        elif operator == 'multi-selection-selected':
            condition_collection = condition_attributes.get('selections') or {}
        elif operator == 'scale-selected':
            condition_collection = condition_attributes.get('scales') or {}
        elif operator == 'single-selection-selected':
            condition_collection = condition_attributes.get('selections') or {}
        else:
            raise Exception('Found unhandled attribute data')
        condition_value = condition_collection.get('values') or []
        operatorModifier = 'every' if condition_collection.get('test_every') else 'some'

        conditions = [
            dict(
                key=legacy_condition['key'],
                conjunctionOperator=legacy_conditions['operator'],
                order=1,
                invert=invert,
                operatorModifier=operatorModifier,
                operator=CONDITIONAL_OPERATOR_MAP[(legacy_condition['widget_id'], legacy_condition['condition_type'])],
                value=condition_value,
            )
        ]

        new_widget = Widget(
            analysis_framework_id=conditional_widget.analysis_framework_id,
            key=widget_data['key'],
            widget_id=widget_data['widget_id'],
            title=widget_data['title'],
            properties=widget_data['properties'],
            conditional_parent_widget=parent_widget,
            conditional_conditions=conditions,
        )
        yield new_widget


def get_attribute_from_conditional_data(widget_qs, attribute):
    conditional_data = copy.deepcopy(attribute.data or {})
    conditional_value = (conditional_data or {}).get('value')
    if conditional_value in [None, {}] or 'selected_widget_key' not in conditional_value:
        return
    selected_widget_key = conditional_value['selected_widget_key']
    selected_widget = widget_qs.get(key=selected_widget_key)
    value = conditional_value.get(selected_widget_key)
    data = (value or {}).get('data') or {}
    return Attribute(
        entry=attribute.entry,
        widget=selected_widget,
        data=data,
    )


def get_number_matrix_widget_data(widget_data):
    rows = {}
    columns = {}
    if widget_data:
        for row in widget_data.get('row_headers'):
            rows[row['key']] = row['title']
        for column in widget_data.get('column_headers'):
            columns[column['key']] = column['title']
    return {
        'rows': rows,
        'columns': columns,
    }


def get_number_matrix_attribute_data(widget_data, attribute_value):
    extracted_data = []
    if attribute_value:
        for row_key, row_data in attribute_value.items():
            row_label = widget_data['rows'].get(row_key, 'N/A')
            if not row_data:
                continue
            for column_key, value in row_data.items():
                column_label = widget_data['columns'].get(column_key, 'N/A')
                extracted_data.append(f'({row_label}, {column_label}, {value})')
    return ','.join(extracted_data)


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
            for index, attribute in enumerate(required_attribute_qs.iterator(chunk_size=1000)):
                # Update properties.
                old_data = copy.deepcopy(attribute.data or {})
                attribute.data = attribute_data_convertor(old_data)
                attribute.data['old_data'] = old_data  # Clean-up this later.
                attribute.widget_version = self.CURRENT_VERSION
                # Save
                attribute.save(update_fields=('data', 'widget_version',))
                print(f'-- Saved ({index})/({total})', end='\r')
        print('')

        # Conditional Widgets
        conditional_widget_qs = widget_qs.filter(widget_id=Widget.WidgetType.CONDITIONAL)
        total = conditional_widget_qs.count()
        print(f'Conditional Widgets (Total: {total})')
        for index, conditional_widget in enumerate(conditional_widget_qs.all(), 1):
            for widget in get_widgets_from_conditional(conditional_widget):
                # Update properties.
                if conditional_widget.properties.get('added_from') == 'overview':  # Requires section
                    widget.section = self.get_section_for_af_id(widget.analysis_framework_id)
                old_properties = copy.deepcopy(widget.properties.get('data') or {})
                widget_property_convertor = WIDGET_MIGRATION_MAP.get(widget.widget_id)
                if widget_property_convertor is not None:
                    widget.properties = widget_property_convertor(old_properties)
                widget.properties['from_conditional_widget'] = True
                widget.version = self.CURRENT_VERSION
                # Save
                widget.save()
            conditional_widget.properties = {'old_data': conditional_widget.properties}
            conditional_widget.version = self.CURRENT_VERSION
            conditional_widget.save(update_fields=('version',))
            print(f'-- Saved ({index})/({total})', end='\r')
        print('')

        # Migrate Conditional Entry Attribute Data
        conditional_attribute_qs = attribute_qs.filter(widget__widget_id=Widget.WidgetType.CONDITIONAL)
        total = conditional_attribute_qs.count()
        print(f'Conditional Entry Attributes (Total: {total})')
        for index, attribute in enumerate(conditional_attribute_qs.iterator(chunk_size=1000)):
            # Update properties.
            try:
                new_attribute = get_attribute_from_conditional_data(
                    Widget.objects.filter(analysis_framework_id=attribute.widget.analysis_framework_id),
                    attribute,
                )
            except Widget.DoesNotExist:
                continue
            if new_attribute is not None:
                attribute_data_convertor = ATTRIBUTE_MIGRATION_MAP.get(new_attribute.widget.widget_id)
                if attribute_data_convertor is not None:
                    new_attribute.data = attribute_data_convertor(copy.deepcopy(new_attribute.data))
                new_attribute.widget_version = self.CURRENT_VERSION
                new_attribute.save()
            attribute.data = {'old_data': attribute.data}
            attribute.widget_version = self.CURRENT_VERSION
            attribute.save(update_fields=('data', 'widget_version',))
            print(f'-- Saved ({index})/({total})', end='\r')
        print('')

        # Now migrate all number_matrix to Text
        number_matrix_widget_qs = widget_qs.filter(widget_id=Widget.WidgetType.NUMBER_MATRIX)
        total = number_matrix_widget_qs.count()
        print(f'Number Matrix Widget (Total: {total})')
        for index, widget in enumerate(number_matrix_widget_qs.iterator(chunk_size=1000)):
            widget.title = f'{widget.title} (Previously Number Matrix)'
            widget.widget_id = Widget.WidgetType.TEXT
            if widget.properties.get('added_from') == 'overview':  # Requires section
                widget.section = self.get_section_for_af_id(widget.analysis_framework_id)
            widget.properties = {
                'migrated_from_number_matrix': True,
                'old_data': copy.deepcopy(widget.properties),
            }
            widget.version = self.CURRENT_VERSION
            widget.save(update_fields=('title', 'widget_id', 'properties', 'version', 'section'))
            print(f'-- Saved ({index})/({total})', end='\r')
        print('')

        # Migrate Number Matrix Entry Attribute Data
        number_matrix_attribute_qs = attribute_qs.filter(widget__properties__migrated_from_number_matrix=True)
        total = number_matrix_attribute_qs.count()
        if total:
            number_matrix_widget_label_map = {}
            for widget in Widget.objects.filter(properties__migrated_from_number_matrix=True):
                widget_data = (widget.properties and widget.properties.get('old_data', {}).get('data'))
                number_matrix_widget_label_map[widget.pk] = get_number_matrix_widget_data(widget_data)

            print(f'Number Matrix Entry Attributes (Total: {total})')
            for index, attribute in enumerate(number_matrix_attribute_qs.iterator(chunk_size=1000)):
                attribute.data = {
                    'value': get_number_matrix_attribute_data(
                        number_matrix_widget_label_map[attribute.widget_id],
                        (attribute.data or {}).get('value'),
                    ),
                    'old_data': attribute.data,
                }
                attribute.widget_version = self.CURRENT_VERSION
                attribute.save(update_fields=('data', 'widget_version',))
                print(f'-- Saved ({index})/({total})', end='\r')
            print('')

        # Finally just update for this widgets (Not changes are required for this widgets)
        print('Update normal widgets:')
        print(
            widget_qs.filter(
                widget_id__in=[
                    Widget.WidgetType.DATE,
                    Widget.WidgetType.DATE_RANGE,
                    Widget.WidgetType.TIME,
                    Widget.WidgetType.TIME_RANGE,
                    Widget.WidgetType.NUMBER,
                    Widget.WidgetType.GEO,
                    Widget.WidgetType.TEXT,
                    # Deprecated widgets
                    Widget.WidgetType.EXCERPT,
                ]
            ).update(version=1)
        )

        # Just update for this widget's attributes (Not changes are required for this widgets)
        print('Update normal attributes:')
        print(
            attribute_qs.filter(
                widget__widget_id__in=[
                    Widget.WidgetType.DATE,
                    Widget.WidgetType.TIME,
                    Widget.WidgetType.NUMBER,
                    Widget.WidgetType.TEXT,
                    Widget.WidgetType.MATRIX1D,
                    Widget.WidgetType.MATRIX2D,
                    Widget.WidgetType.MULTISELECT,
                    Widget.WidgetType.SELECT,
                    Widget.WidgetType.ORGANIGRAM,
                    Widget.WidgetType.SCALE,
                    # Deprecated widgets
                    Widget.WidgetType.EXCERPT,
                ]
            ).update(widget_version=1)
        )


def print_property(widget):
    import json
    print('-' * 22)
    print(json.dumps(widget.properties, indent=2))


def print_attribute_data(widget):
    import json
    print('-' * 22)
    print(json.dumps(widget.data, indent=2))
