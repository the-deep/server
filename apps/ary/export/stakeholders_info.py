from ary.models import MetadataField


STAKEHOLDERS_SOURCE_TYPES = [MetadataField.ORGANIZATIONS]

default_values = {
    'stakeholders': None,
}


def get_stakeholders_info(assessment):
    # TODO: is meta group dynamic?
    stakeholders_data_group = assessment.get_metadata_json().get('Stakeholders')
    added_value = []
    stakeholders_info = []
    for data in stakeholders_data_group:
        if (
            data['schema']['source_type'] in STAKEHOLDERS_SOURCE_TYPES and
            data['schema']['type'] == MetadataField.MULTISELECT
        ):
            for value in data['value']:
                key = value['key']
                if key not in added_value:
                    added_value.append(key)
                    stakeholders_info.append({
                        'name': value['name'],
                        'type': value['type'],
                    })

    return {
        'stakeholders': stakeholders_info,
    }
