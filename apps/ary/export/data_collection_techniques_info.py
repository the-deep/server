default_values = {
}


def format_value(val):
    if isinstance(val, list):
        return ','.join(val)
    if val is None:
        val = ''
    return str(val)


def get_data_collection_techniques_info(assessment):
    attributes = assessment.get_methodology_json().get('Attributes') or []
    data = []

    for attribute in attributes:
        _data = {}
        for methodology_fields in attribute.values():
            for field in methodology_fields:
                _data[field['schema']['name']] = format_value(field['value'])
        data.append(_data)

    return {
        'data_collection_technique': data,
    }
