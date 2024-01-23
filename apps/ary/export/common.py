from datetime import datetime
from utils.common import combine_dicts as _combine_dicts, deep_date_format
from assessment_registry.models import AssessmentRegistry

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
    return deep_date_format(datetime.strptime(datestr, ISO_FORMAT))


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


def get_languages(assessment):
    all_language = {choice.value: choice.label for choice in AssessmentRegistry.Language}
    languages_raw = [all_language.get(lang) for lang in assessment.language]
    assessment_language = {}
    for k, lang in all_language.items():
        if lang in languages_raw:
            assessment_language[all_language[k]] = 1
        else:
            assessment_language[all_language[k]] = 0
    return assessment_language


def get_assessment_meta(assessment):
    lead = assessment.lead
    admin_levels = set(
        [geo_area.admin_level.region.title for geo_area in assessment.locations.all() if geo_area.admin_level.level == 0]
    )

    return {
        'lead': {
            'date_of_lead_publication': deep_date_format(lead.published_on),
            'unique_assessment_id': assessment.id,
            'imported_by': ', '.join([user.username for user in lead.assignee.all()]),
            'lead_title': lead.title,
            'url': lead.url,
            'source': lead.get_source_display(),
        },

        'background': {
            'country': ','.join(admin_levels),
            'crisis_type': assessment.get_bg_crisis_type_display(),
            'crisis_start_date': assessment.bg_crisis_start_date.strftime("%d-%m-%Y") if
            assessment.bg_crisis_start_date else assessment.bg_crisis_start_date,
            'preparedness': assessment.get_bg_preparedness_display(),
            'external_support': assessment.get_external_support_display(),
            'coordination': assessment.get_coordinated_joint_display(),
            'cost_estimates_in_USD': assessment.cost_estimates_usd,
        },

        'details': {
            'type': assessment.get_details_type_display(),
            'family': assessment.get_family_display(),
            'frequency': assessment.get_frequency_display(),
            'confidentiality': assessment.get_confidentiality_display(),
            'number_of_pages': assessment.no_of_pages,
        },

        'language': get_languages(assessment),

        'dates': {
            'data_collection_start_date': assessment.data_collection_start_date.strftime("%d-%m-%Y") if
            assessment.data_collection_start_date else assessment.data_collection_start_date,
            'data_collection_end_date': assessment.data_collection_end_date.strftime("%d-%m-%Y") if
            assessment.data_collection_end_date else assessment.data_collection_end_date,
            'publication_date': assessment.publication_date.strftime("%d-%m-%Y") if
            assessment.publication_date else assessment.publication_date
        },
    }
