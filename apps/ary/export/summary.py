from utils.common import combine_dicts
from ary.models import MethodologyField


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

    methodology = assessment.get_metadata_json()
    attrs = combine_dicts(methodology['Attributes'])
    collection_techniques = combine_dicts(attrs['Collection Technique'])

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
        'focuces': {},
        'sectors': {},
        'affected_groups': {},
        'location': {},
        'methodology_content': {},
    }
    return data
