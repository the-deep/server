from datetime import datetime
from utils.common import combine_dicts as _combine_dicts

DATE_FORMAT = '%d-%m-%Y'
ISO_FORMAT = '%Y-%m-%d'


def combine_dicts(dict_list):
    return _combine_dicts(
        [
            {
                _dict['schema']['name']: _dict
            }
            for _dict in dict_list]
    )


def str_to_dmy_date(datestr):
    """Uses DATE_FORMAT"""
    if not datestr:
        return None
    return datetime.strptime(datestr, ISO_FORMAT).strftime(DATE_FORMAT)


def get_assessment_meta(assessment):
    lead = assessment.lead
    metadata = assessment.get_metadata_json()
    metadata_bg = combine_dicts(metadata['Background'])
    metadata_dates = combine_dicts(metadata['Dates'])
    metadata_details = combine_dicts(
        metadata.get('Type', []) + metadata['Status'] + metadata['Report Details']
    )

    return {
        'lead': {
            'date_of_lead_publication': lead.published_on.strftime(DATE_FORMAT),
            'unique_assessment_id': assessment.id,  # TODO: something else like id hash
            'imported_by': ', '.join([user.username for user in lead.assignee.all()]),
            'lead_title': lead.title,
            'url': lead.url,
            'source': lead.source,
        },

        'background': {
            'country': ','.join(metadata_bg.get('Country', [])),
            'crisis_type': metadata_bg.get('Crisis Type'),
            'crisis_start_date': str_to_dmy_date(metadata_bg.get('Crisis Start Date', {}).get('value')),
            'preparedness': metadata_bg.get('Preparedness'),
            'external_support': ','.join(metadata_bg.get('External Support', [])),
            'coordination': ','.join(metadata_bg.get('Coordination', [])),
            'cost_estimates_in_USD': metadata_bg.get('Cost Estimates in USD'),
        },

        'details': {
            'type': metadata_details['Type'],
            'family': metadata_details['Family'],
            'status': metadata_details['Status'],
            'frequency': metadata_details['Frequency'],
            'confidentiality': metadata_details['Confidentiality'],
            'number_of_pages': metadata_details['Number of Pages'],
        },

        'language': {
            x: 1 for x in metadata_details['Language']
        },

        'dates': {
            'data_collection_start_date': metadata_dates['Start Date'],
            'data_collection_end_date': metadata_dates['End Date'],
            'publication_start_date': metadata_dates['Publication']['from'],
            'publication_end_date': metadata_dates['Publication']['to']
        },
    }
