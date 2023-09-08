from ary.models import AffectedGroup


default_values = {
}

from assessment_registry.models import AssessmentRegistry
# NOTE: This is also used in entries word/pdf exporter
def get_affected_groups_info(assessment):
#    template = assessment.project.assessment_template
#    aff_data = assessment.get_methodology_json().get('Affected Groups') or []
#
#    root_affected_group = AffectedGroup.objects.filter(
#        template=template, parent=None
#    ).first()
#
#    child_list = root_affected_group.get_children_list() if root_affected_group else []
#
#    all_affected_groups = {
#        x['id']: x
#        for x in child_list
#    }
#
#    # get max order
#    max_level = max([len(v['parents']) for k, v in all_affected_groups.items()])
#
#    data = []
#
#    for item in aff_data:
#        info = all_affected_groups.get(item['key'], {})
#        parents = info.get('parents', [])
#        order = len(parents)
#
#        groups = {f'Level {x+1}': None for x in range(max_level)}
#
#        for i, parent in enumerate(parents):
#            groups[f'Level {order - i}'] = parent
#        data.append(groups)
#
    affected_group_type_dict = {choice.value: choice.label for choice in AssessmentRegistry.AffectedGroupType}
    affected_groups = [affected_group_type_dict.get(status) for status in assessment.affected_groups]
    affected_groups_info =[]
    for item in affected_groups:
        aff_list = item.split('/')
        aff_dict = {}
        for i, aff_grp in enumerate(aff_list):
            aff_dict[f'Level {i+1}']=aff_grp
        affected_groups_info.append(aff_dict)
    return {
        'affected_groups_info': affected_groups_info,
#        'affected_groups_info': [
#            {'Level 1': 'All', 'Level 2': 'Affected', 'Level 3': 'Displaced',
#             'Level 4': 'Migrants', 'Level 5': None},
#            {'Level 1': 'All', 'Level 2': 'Affected', 'Level 3': 'Displaced',
#             'Level 4': 'Refugees', 'Level 5': None
#             }
#        ],
    }
