from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Entry

EntryTagTypeEnum = convert_enum_to_graphene_enum(Entry.TagType, name='EntryTagTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Entry.entry_type, EntryTagTypeEnum),
    )
}
