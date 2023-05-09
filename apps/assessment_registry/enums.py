from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import AssessmentRegistry

CrisisTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.CrisisType, name='CrisisTypeEnum')

PreparednessTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.PreparednessType, name='PreparednessTypeEnum')

ExternalSupportTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.ExternalSupportType, name='ExternalTypeEnum')

CoordinationTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.CoordinationType, name='CoordinationTypeEnum')

DetailTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.Type, name='DetailTypeEnum')

FamilyTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.FamilyType, name='FamilyTypeEnum')

FrequencyTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.FrequencyType, name='FrequencyTypeEnum')

ConfidentialityTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.ConfidentialityType, name='ConfidentialityTypeEnum')

LanguageTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.Language, name='LanguageTypeEnum')

FocusTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.FocusType, name='FocusTypeEnum')

SectorTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.SectorType, name='SectorTypeEnum')

ProtectionInfoTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.ProtectionInfoType, name='ProtectionInfoTypeEnum')

AffectedGroupTypeEnum = convert_enum_to_graphene_enum(AssessmentRegistry.AffectedGroupType, name='AffectedGroupTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (AssessmentRegistry.bg_crisis_type, CrisisTypeEnum),
        (AssessmentRegistry.bg_preparedness, PreparednessTypeEnum),
        (AssessmentRegistry.external_support, ExternalSupportTypeEnum),
        (AssessmentRegistry.coordinated_joint, CoordinationTypeEnum),
        (AssessmentRegistry.details_type, DetailTypeEnum),
        (AssessmentRegistry.family, FamilyTypeEnum),
        (AssessmentRegistry.frequency, FrequencyTypeEnum),
        (AssessmentRegistry.confidentiality, ConfidentialityTypeEnum),
        (AssessmentRegistry.language, LanguageTypeEnum),
        (AssessmentRegistry.focuses, FocusTypeEnum),
        (AssessmentRegistry.sectors, SectorTypeEnum),
        (AssessmentRegistry.protection_info_mgmts, ProtectionInfoTypeEnum),
        (AssessmentRegistry.affected_groups, AffectedGroupTypeEnum),
    )
}
