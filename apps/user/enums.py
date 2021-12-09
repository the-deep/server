from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import User, Profile

UserEmailConditionOptOutEnum = convert_enum_to_graphene_enum(
    Profile.EmailConditionOptOut, name='UserEmailConditionOptOutEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Profile.email_opt_outs, UserEmailConditionOptOutEnum),
    )
}


# Additional enums which doesn't have a field in model but are used in serializer
enum_map.update({
    get_enum_name_from_django_field(
        None,
        field_name='email_opt_outs',  # UserMeSerializer.email_opt_outs
        model_name=User.__name__,
    ): UserEmailConditionOptOutEnum,
})
