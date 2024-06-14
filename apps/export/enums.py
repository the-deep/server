from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import Export, GenericExport

ExportFormatEnum = convert_enum_to_graphene_enum(Export.Format, name="ExportFormatEnum")
ExportStatusEnum = convert_enum_to_graphene_enum(Export.Status, name="ExportStatusEnum")
ExportDataTypeEnum = convert_enum_to_graphene_enum(Export.DataType, name="ExportDataTypeEnum")
ExportExportTypeEnum = convert_enum_to_graphene_enum(Export.ExportType, name="ExportExportTypeEnum")
ExportExcelSelectedStaticColumnEnum = convert_enum_to_graphene_enum(
    Export.StaticColumn,
    name="ExportExcelSelectedStaticColumnEnum",
)
ExportDateFormatEnum = convert_enum_to_graphene_enum(Export.DateFormat, name="ExportDateFormatEnum")
ExportReportCitationStyleEnum = convert_enum_to_graphene_enum(
    Export.CitationStyle,
    name="ExportReportCitationStyleEnum",
)

GenericExportFormatEnum = convert_enum_to_graphene_enum(GenericExport.Format, name="GenericExportFormatEnum")
GenericExportStatusEnum = convert_enum_to_graphene_enum(GenericExport.Status, name="GenericExportStatusEnum")
GenericExportDataTypeEnum = convert_enum_to_graphene_enum(GenericExport.DataType, name="GenericExportDataTypeEnum")

enum_map = {
    # Need to pass model with abstract base class
    get_enum_name_from_django_field(field, model_name=model.__name__): enum
    for model, field, enum in (
        # -- Project Exports
        (Export, Export.format, ExportFormatEnum),
        (Export, Export.status, ExportStatusEnum),
        (Export, Export.type, ExportDataTypeEnum),
        (Export, Export.export_type, ExportExportTypeEnum),
        # -- Generic Exports
        (GenericExport, GenericExport.format, GenericExportFormatEnum),
        (GenericExport, GenericExport.status, GenericExportStatusEnum),
        (GenericExport, GenericExport.type, GenericExportDataTypeEnum),
    )
}

enum_map.update(
    {
        get_enum_name_from_django_field(
            None,
            field_name="static_column",
            serializer_name="ExportExcelSelectedColumnSerializer",
        ): ExportExcelSelectedStaticColumnEnum,
        get_enum_name_from_django_field(
            None,
            field_name="date_format",
            serializer_name="ExportExtraOptionsSerializer",
        ): ExportDateFormatEnum,
        get_enum_name_from_django_field(
            None,
            field_name="report_citation_style",
            serializer_name="ExportExtraOptionsSerializer",
        ): ExportReportCitationStyleEnum,
    }
)
