from ary.models import AffectedGroup


def get_affected_groups_info(assessment):
    template = assessment.lead.project.assessment_template
    aff_data = assessment.get_methodology_json()['Affected Groups']

    root_affected_group = AffectedGroup.objects.filter(
        template=template, parent=None
    ).first()

    child_list = root_affected_group.get_children_list() if root_affected_group else []

    all_affected_groups = {
        x['id']: x
        for x in child_list
    }

    # get max order
    max_level = max([len(v['parents']) for k, v in all_affected_groups.items()])

    data = {
        f'Level {x+1}': []
        for x in range(max_level)
    }

    for item in aff_data:
        info = all_affected_groups.get(item['key'], {})
        parents = info.get('parents', [])
        order = item['order']

        for i, parent in enumerate(parents):
            data[f'Level {order - i}'].append(parent)

    return {
        'affected_groups_info': data,
    }
