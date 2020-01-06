from functools import reduce

from .common import (
    get_assessment_meta,
    get_planned_assessment_meta,
    default_values as common_defaults,
)
from .stakeholders_info import (
    get_stakeholders_info,
    default_values as stakeholders_defaults
)
from .summary import (
    get_assessment_export_summary,
    default_values as summary_defaults
)
from .locations_info import (
    get_locations_info,
    default_values as locations_defaults
)
from .data_collection_techniques_info import (
    get_data_collection_techniques_info,
    default_values as collection_defaults
)
from .affected_groups_info import (
    get_affected_groups_info,
    default_values as affected_defaults
)


def get_export_data(assessment, planned_assessment=False):
    if planned_assessment:
        meta_data = get_planned_assessment_meta(assessment)
    planned_assessment_data = {
        'summary': {
            **meta_data,
            **get_assessment_export_summary(assessment, planned_assessment),
        },
        'stakeholders': {
            **meta_data,
            **get_stakeholders_info(assessment),
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

    if planned_assessment:
        return planned_assessment_data

    meta_data = get_assessment_meta(assessment)

    # Planned assessment does not have metadata in summary, so add it now
    # which will be reused for normal assessment export data
    planned_assessment['summary'].update(meta_data)

    questionnaire = assessment.get_questionnaire_json()

    return {
        **planned_assessment_data,
        'data_collection_technique': {
            **meta_data,
            **get_data_collection_techniques_info(assessment),
        },
        'stakeholders': {
            **meta_data,
            **get_stakeholders_info(assessment),
        },
        'locations': {
            **meta_data,
            **get_locations_info(assessment),
        },
        'affected_groups': {
            **meta_data,
            **get_affected_groups_info(assessment),
        },
        # Add HNO and CNA
        'hno': {
            **meta_data,
            **get_assessment_export_summary(assessment),
            **questionnaire['hno']
        },
        'cna': {
            **meta_data,
            **get_assessment_export_summary(assessment),
            **questionnaire['cna']
        }
    }


def replicate_other_col_groups(sheet_data, column_group):
    group_data = sheet_data.pop(column_group)
    size = len(group_data)

    new_sheet_data = {}
    for other_col_group, col_data in sheet_data.items():
        new_sheet_data[other_col_group] = [col_data] * (size or 1)  # if size zero, nothing will be present
    new_sheet_data[column_group] = group_data
    return new_sheet_data


def normalize_assessment(assessment_export_data, planned_assessment=False):
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

    planned_assessment_data = {
        'summary': {k: [v] for k, v in assessment_export_data['summary'].items()},
        'stakeholders': new_stakeholders_sheet,
        'affected_groups': new_affected_sheet,
        'locations': new_locations_sheet,
    }
    if planned_assessment:
        return planned_assessment_data

    # Normailze Data Collection Techniques
    techniques_sheet = assessment_export_data['data_collection_technique']
    new_techniques_sheet = replicate_other_col_groups(techniques_sheet, 'data_collection_technique')

    return {
        **planned_assessment_data,
        'data_collection_technique': new_techniques_sheet,
        'hno': {k: [v] for k, v in assessment_export_data['hno'].items()},
        'cna': {k: [v] for k, v in assessment_export_data['cna'].items()},
    }


DEFAULTS = {
    'summary': summary_defaults,
    'stakeholders': stakeholders_defaults,
    'data_collection_technique': collection_defaults,
    'locations': locations_defaults,
    'affected_groups': affected_defaults,
}
for k, v in DEFAULTS.items():
    v.update(common_defaults)


# NOTE: This is magic function, but make it simpler
def add_assessment_to_rows(sheets, assessment, planned_assessment=False):
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
    def add_new_keys(keys, data, default=None):
        if not keys:
            return data
        if isinstance(data, dict):
            return {**data, **{x: default for x in keys}}
        elif isinstance(data, list):
            return [
                {**(x or {}), **{k: default for k in keys}}
                for x in data
            ]
        return data

    normalized_assessment = normalize_assessment(get_export_data(assessment, planned_assessment), planned_assessment)

    new_sheets = {}

    for sheet, sheet_data in sheets.items():
        new_sheets[sheet] = {}
        assessment_sheet = normalized_assessment[sheet]
        sheet_data_len = 0

        for col, columns_data in sheet_data.items():
            sheet_data_len = len(columns_data)  # this is same for every columns data
            assessment_col_data = assessment_sheet.get(col)
            # If columns data is empty, add new data to account for empty row
            # assessment data is then appended
            if not columns_data:
                if isinstance(assessment_col_data, list):
                    # TODO: Try to check if it should be dict or None
                    ass_sample = assessment_col_data[0] if assessment_col_data else {}
                else:
                    ass_sample = assessment_col_data
                if isinstance(ass_sample, dict):
                    columns_data = [{}]
                else:
                    columns_data = [None]

            columns_data = [columns_data] if not isinstance(columns_data, list) else columns_data

            assessment_col_data = [assessment_col_data]\
                if not isinstance(assessment_col_data, list) else assessment_col_data

            if isinstance(columns_data[0], dict):
                # if assessment data empty, add empty dict
                if not assessment_col_data:
                    assessment_col_data = [{}]
                assessment_row_keys = set((assessment_col_data[0] or {}).keys())\
                    if assessment_col_data else set()

                sheet_row_keys = set(columns_data[0].keys())
                new_ass_keys = assessment_row_keys.difference(sheet_row_keys)
                new_sheet_keys = sheet_row_keys.difference(assessment_row_keys)

                if new_ass_keys:
                    # Add the key to each row in  column data
                    default = DEFAULTS[sheet].get(col, DEFAULTS[sheet].get('*'))
                    columns_data = add_new_keys(new_ass_keys, columns_data, default)

                if new_sheet_keys:
                    # Add new keys to assessment data
                    default = DEFAULTS[sheet].get(col, DEFAULTS[sheet].get('*'))
                    assessment_col_data = add_new_keys(
                        new_sheet_keys, assessment_col_data, default
                    )
            # Now all the data is normalized(have same keys)
            # Append assessment data to col data
            columns_data.extend(assessment_col_data)
            new_sheets[sheet][col] = columns_data

        # Add columns not present in sheet_data but in assessment
        sheet_cols = set(sheet_data.keys())
        assessment_cols = set(assessment_sheet.keys())
        new_cols = assessment_cols.difference(sheet_cols)

        newcols_data = {}
        for newcol in new_cols:
            coldata = assessment_sheet[newcol]
            # NOTE: if coldata is empty, we assume it contains dict
            if not coldata:
                coldata = [{}]
            if not isinstance(coldata[0], dict):
                newcols_data[newcol] = [*[None] * (sheet_data_len), *coldata]
            else:
                empty_data = {
                    key: None
                    for key in coldata[0].keys()
                }
                newcols_data[newcol] = [dict(empty_data) for _ in range(sheet_data_len)]
                newcols_data[newcol].extend(coldata)

        new_sheets[sheet].update(newcols_data)

    return new_sheets


def get_export_data_for_assessments(assessments):
    if not assessments:
        return {}
    data = normalize_assessment(get_export_data(assessments[0]))
    return reduce(add_assessment_to_rows, assessments[1:], data)


def get_export_data_for_planned_assessments(planned_assessments):
    if not planned_assessments:
        return {}
    data = normalize_assessment(get_export_data(planned_assessments[0], True), True)

    return reduce(
        lambda a, x: add_assessment_to_rows(a, x, True),
        planned_assessments[1:],
        data
    )
