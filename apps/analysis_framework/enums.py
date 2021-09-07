from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Widget, Filter


WidgetWidgetTypeEnum = convert_enum_to_graphene_enum(Widget.WidgetType, name='WidgetWidgetTypeEnum')
WidgetWidthTypeEnum = convert_enum_to_graphene_enum(Widget.WidthType, name='WidgetWidthTypeEnum')
WidgetFilterTypeEnum = convert_enum_to_graphene_enum(Filter.FilterType, name='WidgetFilterTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Widget.widget_id, WidgetWidgetTypeEnum),
        (Widget.width, WidgetWidthTypeEnum),
        (Filter.filter_type, WidgetFilterTypeEnum),
    )
}
