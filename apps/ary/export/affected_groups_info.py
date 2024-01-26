from assessment_registry.models import AssessmentRegistry


default_values = {
}


def get_affected_groups_info(assessment):
    affected_group_type_dict = {choice.value: choice.label for choice in AssessmentRegistry.AffectedGroupType}
    affected_groups = [affected_group_type_dict.get(group) for group in assessment.affected_groups if group]
    max_level = max([len(v.split('/')) for k, v in AssessmentRegistry.AffectedGroupType.choices])
    levels = [f'Level {i+1}' for i in range(max_level)]
    affected_grp_list = []
    for group in affected_groups:
        group = group.split("/")
        group_dict = {}
        for i, level in enumerate(levels):
            if i < len(group):
                group_dict[level] = group[i]
            else:
                group_dict[level] = None
        affected_grp_list.append(group_dict)

    return {
        'affected_groups_info': affected_grp_list,
    }
