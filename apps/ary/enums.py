from utils.graphene.enums import convert_enum_to_graphene_enum

from .models import MethodologyProtectionInfo


AssessmentMethodologyProtectionInfoEnum = convert_enum_to_graphene_enum(
    MethodologyProtectionInfo, name='AssessmentMethodologyProtectionInfoEnum')

enum_map = {
    'UnusedAssessmentMethodologyProtectionInfo': AssessmentMethodologyProtectionInfoEnum,
}
