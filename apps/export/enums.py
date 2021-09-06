from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Export

ExportFormatEnum = convert_enum_to_graphene_enum(Export.Format, name='ExportFormatEnum')
ExportStatusEnum = convert_enum_to_graphene_enum(Export.Status, name='ExportStatusEnum')
ExportDataTypeEnum = convert_enum_to_graphene_enum(Export.DataType, name='ExportDataTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Export.format, ExportFormatEnum),
        (Export.status, ExportStatusEnum),
        (Export.type, ExportDataTypeEnum),
    )
}
