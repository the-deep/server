def get_affected_groups_info(assessment):
    aff_data = assessment.get_methodology_json()['Affected Groups']
    data = {}

    # TODO: Do hierarchical select similar to entry export for geo regions
    # NOTE: Should have same logic similar to location for ary export
    for item in aff_data:
        if data.get(item['order']):
            data[item['order']].append(item['title'])
        else:
            data[item['order']] = [item['title']]

    return {
        'affected_groups_info': data,
    }
