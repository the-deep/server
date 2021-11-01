from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import DiscardedEntry

DiscardedEntryTagTypeEnum = convert_enum_to_graphene_enum(DiscardedEntry.TagType, name='DiscardedEntryTagTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (DiscardedEntry.tag, DiscardedEntryTagTypeEnum),
    )
}
