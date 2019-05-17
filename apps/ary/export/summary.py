from utils.common import combine_dicts
from ary.models import (
    MethodologyField,
    Focus,
    Sector,
    AffectedGroup,
)


def get_assessment_export_summary(assessment):
    """
    Returns json summary of all the tabs in the assessment including lead info
    """
    lead = assessment.lead
    template = lead.project.assessment_template

    additional_documents = assessment.metadata['additional_documents']

    all_collection_fields = MethodologyField.objects.filter(
        group__template=template,
        title='Data Collection Technique'
    )
    if not all_collection_fields:
        all_collection_techniques = {}
    else:
        all_collection_techniques = {
            x.title: 0
            for x in all_collection_fields[0].options.all()
        }

    metadata = assessment.get_metadata_json()
    attrs = combine_dicts(metadata['Attributes'])
    collection_techniques = combine_dicts(attrs['Collection Technique'])

    methodology = assessment.get_methodology_json()

    focuses = [x.title for x in Focus.objects.filter(template=template)]
    selected_focuses = set(methodology['Focuses'])

    sectors = [x.title for x in Sector.objects.filter(template=template)]
    selected_sectors = set(methodology['Sectors'])

    root_affected_group = AffectedGroup.objects.filter(template=template, parent=None)
    all_affected_groups = root_affected_group.get_children_list() if root_affected_group else []

    selected_affected_groups_ids = {x['key'] for x in methodology['Affected Groups']}

    locations = assessment.methodology['locations']
    # TODO: Get regions and admin levels

    data = {
        'stakeholders': {},  # TODO

        'additional_documents': {
            'Executive Summary': 1 if additional_documents['executive_summary'] else 0,
            'Assessment Database': 1 if additional_documents['assessment_data'] else 0,
            'Questionnaire': 1 if additional_documents['questionnaire'] else 0,
            'Miscellaneous': 1 if additional_documents['misc'] else 0,
        },

        'data_collection_technique': {
            **all_collection_techniques,
            **{x: 1 for x in collection_techniques}
        },
        'focuses': {
            x: 1 if x in selected_focuses else 0
            for x in focuses
        },
        'sectors': {
            x: 1 if x in selected_sectors else 0
            for x in sectors
        },
        'affected_groups': {
            x: 1 if x['id'] in selected_affected_groups_ids else 0
            for x in all_affected_groups
        },
        'location': {
        },
        'methodology_content': {
            'objectives': 1 if methodology['Objectives'] else 0,
            'data_collection_techniques': 1 if methodology['Data Collection Techniques'] else 0,
            'sampling': 1 if methodology['Sampling'] else 0,
            'limitations': 1 if methodology['Limitations'] else 0,
        },
    }
    return data
