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


def get_value(d, key, default=None):
    return d.get(key, {}).get('value', default)


def get_name_values(data_dict, keys):
    if not isinstance(keys, list):
        keys = [keys]
    return {
        x['schema']['name']: x['value']
        for key in keys
        for x in data_dict.get(key, [])
    }


def get_name_values_options(data_dict, keys):
    if not isinstance(keys, list):
        keys = [keys]
    return {
        x['schema']['name']: {
            'value': x['value'],
            'options': x['schema']['options']
        }
        for key in keys
        for x in data_dict.get(key, [])
    }


def populate_with_all_values(d, key, default=None):
    """This gets options and returns dict containing {value: count}"""
    options = {
        v: 0 for k, v in d.get(key, {}).get('options', {}).items()
    }
    return {
        **options,
        **{
            x: 1
            for x in d.get(key, {}).get('value', default)
        }
    }


default_values = {
    'language': 0,
}


def get_assessment_meta(assessment):
    lead = assessment.lead
    metadata = assessment.get_metadata_json()

    metadata_bg = get_name_values(metadata, 'Background')
    metadata_dates = get_name_values(metadata, 'Dates')

    metadata_details = get_name_values_options(metadata, ['Details', 'Status', 'Report Details'])

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
            'type': get_value(metadata_details, 'Type'),
            'family': get_value(metadata_details, 'Family'),
            'status': get_value(metadata_details, 'Status'),
            'frequency': get_value(metadata_details, 'Frequency'),
            'confidentiality': get_value(metadata_details, 'Confidentiality'),
            'number_of_pages': get_value(metadata_details, 'Number of Pages'),
        },

        'language': populate_with_all_values(metadata_details, 'Language', []),

        'dates': {
            'data_collection_start_date': str_to_dmy_date(metadata_dates.get('Data Collection Start Date')),
            'data_collection_end_date': str_to_dmy_date(metadata_dates.get('Data Collection End Date')),
            'publication_date': str_to_dmy_date(metadata_dates.get('Publication Date')),
        },
    }
