from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Export

ExportFormatEnum = convert_enum_to_graphene_enum(Export.Format, name='ExportFormatEnum')
ExportStatusEnum = convert_enum_to_graphene_enum(Export.Status, name='ExportStatusEnum')
ExportDataTypeEnum = convert_enum_to_graphene_enum(Export.DataType, name='ExportDataTypeEnum')
ExportExportTypeEnum = convert_enum_to_graphene_enum(Export.ExportType, name='ExportExportTypeEnum')

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (Export.format, ExportFormatEnum),
        (Export.status, ExportStatusEnum),
        (Export.type, ExportDataTypeEnum),
        (Export.export_type, ExportExportTypeEnum)
    )
}
