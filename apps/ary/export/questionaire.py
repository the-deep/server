from assessment_registry.models import Answer


def get_questionaire(assessment):
    answers = Answer.objects.filter(assessment_registry=assessment)

    sub_sector_list_set = set([answer.question.get_sub_sector_display() for answer in answers])
    questionaire_dict = {}
    for sub_sector in sub_sector_list_set:
        questionaire_dict[sub_sector] = {
            answer.question.question: 1 if answer.answer else 0
            for answer in answers
            if answer.question.get_sub_sector_display() == sub_sector
        }

    return questionaire_dict
