from functools import reduce

from .common import get_assessment_meta
from .stakeholders_info import get_stakeholders_info  # noqa:F401
from .summary import get_assessment_export_summary  # noqa:F401
from .locations_info import get_locations_info  # noqa:F401
from .data_collection_techniques_info import get_data_collection_techniques_info  # noqa:F401
from .affected_groups_info import get_affected_groups_info  # noqa:F401
from .scoring import get_scoring  # noqa:F401


def get_export_data(assessment):
    meta_data = get_assessment_meta(assessment)
    return {
        'summary': {
            **meta_data,
            **get_assessment_export_summary(assessment),
        },
        'data_collection_technique': {
            **meta_data,
            **get_data_collection_techniques_info(assessment),
        },
        'stakeholders': {
            **meta_data,
            **get_stakeholders_info(assessment),
        },
        'scoring': {
            **meta_data,
            **get_scoring(assessment),
        },
        'locations': {
            **meta_data,
            **get_locations_info(assessment),
        },
        'affected_groups': {
            **meta_data,
            **get_affected_groups_info(assessment),
        },
    }


def replicate_other_col_groups(sheet_data, column_group):
    group_data = sheet_data.pop(column_group)
    size = len(group_data)

    new_sheet_data = {}
    for other_col_group, col_data in sheet_data.items():
        new_sheet_data[other_col_group] = [col_data] * size
    new_sheet_data[column_group] = group_data
    return new_sheet_data


def normalize_assessment(assessment_export_data):
    """
    Normally each field has single value, but when there are multiple values,
    each of the values are replicated that many times
    """
    # Normalize each of the sheets
    # Summary need not be normalized

    # Normalize stakeholders
    stakeholders_sheet = assessment_export_data['stakeholders']
    new_stakeholders_sheet = replicate_other_col_groups(stakeholders_sheet, 'stakeholders')

    # Normalize Locations
    locations_sheet = assessment_export_data['locations']
    new_locations_sheet = replicate_other_col_groups(locations_sheet, 'locations')

    # Normalize Affected groups
    affected_sheet = assessment_export_data['affected_groups']
    new_affected_sheet = replicate_other_col_groups(affected_sheet, 'affected_groups_info')

    # Normailze Data Collection Techniques
    techniques_sheet = assessment_export_data['data_collection_technique']
    new_techniques_sheet = replicate_other_col_groups(techniques_sheet, 'data_collection_technique')

    return {
        'summary': assessment_export_data['summary'],
        'stakeholders': new_stakeholders_sheet,
        'affected_groups': new_affected_sheet,
        'locations': new_locations_sheet,
        'data_collection_technique': new_techniques_sheet,
        'scoring': assessment_export_data['scoring'],
    }


def add_assessment_to_rows(sheets, assessment):
    """
    sheets = {
        sheet1: {
            grouped_col: [
                { col1: val1, col2: val2, col3: val3 },
                { col1: val1, col2: val2, col3: val3 },
                ...
            ]
        },
        sheet2: {
            ...
        }
    }
    NOTE: If assessment has new column name inside grouped cols, the column is
    added to all existing data with None value
    """
    def add_new_keys(keys, data):
        if not keys:
            return data
        if isinstance(data, dict):
            return {**data, **{x: None for x in keys}}
        elif isinstance(data, list):
            return [
                {**(x or {}), **{k: None for k in keys}}
                for x in data
            ]
        return data

    normalized_assessment = normalize_assessment(get_export_data(assessment))

    new_sheets = {}

    for sheet, sheet_data in sheets.items():
        new_sheets[sheet] = {}
        assessment_sheet = normalized_assessment[sheet]

        for grouped_col, columns_data in sheet_data.items():
            assessment_grouped_data = assessment_sheet.get(grouped_col)
            # If columns data is empty, just append assessment row data
            if not columns_data:
                columns_data.append(assessment_grouped_data)
                continue

            columns_data = [columns_data] if not isinstance(columns_data, list) else columns_data

            assessment_grouped_data = [assessment_grouped_data]\
                if not isinstance(assessment_grouped_data, list) else assessment_grouped_data

            if isinstance(columns_data[0], dict):
                assessment_row_keys = set((assessment_grouped_data[0] or {}).keys())\
                    if assessment_grouped_data else set()
                sheet_row_keys = set(columns_data[0].keys())
                new_ass_keys = assessment_row_keys.difference(sheet_row_keys)
                new_sheet_keys = sheet_row_keys.difference(assessment_row_keys)

                if new_ass_keys:
                    # Add the key to each row in  column data
                    columns_data = add_new_keys(new_ass_keys, columns_data)

                if new_sheet_keys:
                    # Add new keys to assessment data
                    assessment_grouped_data = add_new_keys(new_sheet_keys, assessment_grouped_data)
            # Now all the data is normalized(have same keys)
            # Append assessment data to col data
            columns_data.extend(assessment_grouped_data)
            new_sheets[sheet][grouped_col] = columns_data
    return new_sheets


def get_export_data_for_assessments(assessments):
    if not assessments:
        return None
    data = normalize_assessment(get_export_data(assessments[0]))
    return reduce(add_assessment_to_rows, assessments[1:], data)
