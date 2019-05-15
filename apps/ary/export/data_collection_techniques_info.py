def get_data_collection_techniques_info(assessment):
    attributes = assessment.get_methodology_json()['Attributes']
    data = []

    for attribute in attributes:
        _data = {}
        for methodology_fields in attribute.values():
            for field in methodology_fields:
                _data[field['schema']['name']] = field['value']
        data.append(_data)

    return {
        'Data Collection Technique': data,
    }
