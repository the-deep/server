from ary.models import AffectedGroup


default_values = {
}


# NOTE: This is also used in entries word/pdf exporter
def get_affected_groups_info(assessment):
    template = assessment.project.assessment_template
    aff_data = assessment.get_methodology_json().get('Affected Groups') or []

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

    data = []

    for item in aff_data:
        info = all_affected_groups.get(item['key'], {})
        parents = info.get('parents', [])
        order = len(parents)

        groups = {f'Level {x+1}': None for x in range(max_level)}

        for i, parent in enumerate(parents):
            groups[f'Level {order - i}'] = parent
        data.append(groups)

    return {
        'affected_groups_info': data,
    }
