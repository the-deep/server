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


default_values = {
    'language': 0,
}


def get_assessment_meta(assessment):
    lead = assessment.lead
    metadata = assessment.get_metadata_json()

    metadata_bg = {
        x['schema']['name']: x['value']
        for x in metadata['Background']
    }
    metadata_dates = {
        x['schema']['name']: x['value']
        for x in metadata['Dates']
    }
    metadata_details = {
        x['schema']['name']: x['value']
        for x in [
            *metadata.get('Details', []),
            *metadata.get('Status', []),
            *metadata.get('Report Details', [])
        ]
    }
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
            'crisis_start_date': str_to_dmy_date(metadata_bg.get('Crisis Start Date')),
            'preparedness': metadata_bg.get('Preparedness'),
            'external_support': ','.join(metadata_bg.get('External Support', [])),
            'coordination': metadata_bg.get('Coordination'),
            'cost_estimates_in_USD': metadata_bg.get('Cost estimates in USD'),
        },

        'details': {
            'type': metadata_details.get('Type'),
            'family': metadata_details.get('Family'),
            'status': metadata_details.get('Status'),
            'frequency': metadata_details.get('Frequency'),
            'confidentiality': metadata_details.get('Confidentiality'),
            'number_of_pages': metadata_details.get('Number of Pages'),
        },

        'language': {
            x: 1 for x in metadata_details.get('Language', [])
        },

        'dates': {
            'data_collection_start_date': metadata_dates.get('Data Collection Start Date'),
            'data_collection_end_date': metadata_dates.get('Data Collection End Date'),
            'publication_start_date': metadata_dates.get('Publication', {}).get('from'),
            'publication_end_date': metadata_dates.get('Publication', {}).get('to'),
        },
    }
