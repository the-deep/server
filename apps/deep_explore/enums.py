from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import PublicExploreSnapshot

PublicExploreSnapshotTypeEnum = convert_enum_to_graphene_enum(PublicExploreSnapshot.Type, name="PublicExploreSnapshotTypeEnum")
PublicExploreSnapshotGlobalTypeEnum = convert_enum_to_graphene_enum(
    PublicExploreSnapshot.GlobalType, name="PublicExploreSnapshotGlobalTypeEnum"
)


enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (PublicExploreSnapshot.type, PublicExploreSnapshotTypeEnum),
        (PublicExploreSnapshot.global_type, PublicExploreSnapshotGlobalTypeEnum),
    )
}
