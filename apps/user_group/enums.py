from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import GroupMembership

GroupMembershipRoleEnum = convert_enum_to_graphene_enum(GroupMembership.Role, name="GroupMembershipRoleEnum")

enum_map = {get_enum_name_from_django_field(field): enum for field, enum in ((GroupMembership.role, GroupMembershipRoleEnum),)}
