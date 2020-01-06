from geo.models import GeoArea

from ary.models import (
    MethodologyGroup,
    MethodologyOption,
    MetadataField,
    Focus,
    Sector,
    AffectedGroup,
)

from .scoring import get_scoring


# Default values for column groups
# Add other default values as required
default_values = {
    'location': 0,
    'additional_documents': 0,
    'focuses': 0,
    'sectors': 0,
    'affected_groups': 0,
    'methodology_content': 0
}


def get_methodology_summary(assessment):
    methodology = assessment.get_methodology_json()
    groups = MethodologyGroup.objects.filter(template=assessment.project.assessment_template)

    attributes = {}
    groups_options = {
        group.title: MethodologyOption.objects.filter(field__in=group.fields.all())
        for group in groups
    }

    for attr in methodology.get('Attributes', []):
        for group, options in groups_options.items():
            data = attr.get(group) or [{}]
            attr_data = attributes.get(group, {})
            for option in options:
                attr_data[option.title] = attr_data.get(option.title, 0) +\
                    (1 if data[0].get('value') == option.title else 0)
            attributes[group] = attr_data
    return attributes


def get_assessment_export_summary(assessment, planned_assessment=False):
    """
    Returns json summary of all the tabs in the assessment including lead info
    """
    template = assessment.project.assessment_template

    additional_documents = assessment.metadata.get('additional_documents') or {}

    metadata = assessment.get_metadata_json()
    methodology = assessment.get_methodology_json()

    focuses = [x.title for x in Focus.objects.filter(template=template)]
    selected_focuses = set(methodology.get('Focuses') or [])

    sectors = [x.title for x in Sector.objects.filter(template=template)]
    selected_sectors = set(methodology['Sectors'] or [])

    root_affected_group = AffectedGroup.objects.filter(template=template, parent=None).first()
    all_affected_groups = root_affected_group.get_children_list() if root_affected_group else []

    methodology_summary = get_methodology_summary(assessment)

    # All affected groups does not have title, so generate title from parents
    processed_affected_groups = [
        {
            'title': ' and '.join(x['parents'][::-1]),
            'id': x['id']
        } for x in all_affected_groups
    ]

    selected_affected_groups_ids = {x['key'] for x in (methodology['Affected Groups'] or [])}

    locations = assessment.methodology['locations'] or []

    geo_areas = GeoArea.objects.filter(id__in=locations).prefetch_related('admin_level')
    admin_levels = {f'Admin {x}': 0 for x in range(7)}

    for geo in geo_areas:
        level = geo.admin_level.level
        key = f'Admin {level}'
        admin_levels[key] = admin_levels.get(key, 0) + 1

    planned_assessment_info = {
        **methodology_summary,
        'location': admin_levels,
        'focuses': {
            x: 1 if x in selected_focuses else 0
            for x in focuses
        },
        'sectors': {
            x: 1 if x in selected_sectors else 0
            for x in sectors
        },
        'affected_groups': {
            x['title']: 1 if x['id'] in selected_affected_groups_ids else 0
            for x in processed_affected_groups
        },
    }
    if planned_assessment:
        return { 'title': assessment.title, **planned_assessment_info}

    stakeholders = metadata['Stakeholders']
    lead_org = stakeholders[0]
    other_orgs = [x for x in stakeholders[1:]]

    data = {
        'methodology_content': {
            'objectives': 1 if methodology['Objectives'] else 0,
            'data_collection_techniques': 1 if methodology['Data Collection Techniques'] else 0,
            'sampling': 1 if methodology['Sampling'] else 0,
            'limitations': 1 if methodology['Limitations'] else 0,
        },
        'stakeholders': {
            lead_org['schema']['name']: lead_org['value'][0]['name'] if lead_org['value'] else '',
            **{
                x['schema']['name']: len(x['value'])
                if x['schema']['type'] == MetadataField.MULTISELECT else 1
                for x in other_orgs
            }
        },

        'additional_documents': {
            'Executive Summary': 1 if additional_documents.get('executive_summary') else 0,
            'Assessment Database': 1 if additional_documents.get('assessment_data') else 0,
            'Questionnaire': 1 if additional_documents.get('questionnaire') else 0,
            'Miscellaneous': 1 if additional_documents.get('misc') else 0,
        },

        **planned_assessment_info,
        # scoring
        **get_scoring(assessment),
    }
    return data
