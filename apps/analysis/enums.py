from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import (
    AnalysisReportContainer,
    AnalysisReportUpload,
    AnalyticalStatementGeoTask,
    AnalyticalStatementNGram,
    AutomaticSummary,
    DiscardedEntry,
    TopicModel,
)
from .serializers import (
    AnalysisReportBarChartConfigurationSerializer,
    AnalysisReportBorderStyleSerializer,
    AnalysisReportCategoricalLegendStyleSerializer,
    AnalysisReportHeadingConfigurationSerializer,
    AnalysisReportHorizontalAxisSerializer,
    AnalysisReportImageContentStyleSerializer,
    AnalysisReportLineLayerStyleSerializer,
    AnalysisReportMapLayerConfigurationSerializer,
    AnalysisReportSymbolLayerConfigurationSerializer,
    AnalysisReportTextStyleSerializer,
    AnalysisReportVariableSerializer,
    AnalysisReportVerticalAxisSerializer,
    ReportEnum,
)

DiscardedEntryTagTypeEnum = convert_enum_to_graphene_enum(DiscardedEntry.TagType, name="DiscardedEntryTagTypeEnum")

TopicModelStatusEnum = convert_enum_to_graphene_enum(TopicModel.Status, name="TopicModelStatusEnum")

AutomaticSummaryStatusEnum = convert_enum_to_graphene_enum(AutomaticSummary.Status, name="AutomaticSummaryStatusEnum")
AnalyticalStatementNGramStatusEnum = convert_enum_to_graphene_enum(
    AnalyticalStatementNGram.Status, name="AnalyticalStatementNGramStatusEnum"
)
AnalyticalStatementGeoTaskStatusEnum = convert_enum_to_graphene_enum(
    AnalyticalStatementGeoTask.Status, name="AnalyticalStatementGeoTaskStatusEnum"
)

# Analysis Report
AnalysisReportUploadTypeEnum = convert_enum_to_graphene_enum(AnalysisReportUpload.Type, name="AnalysisReportUploadTypeEnum")
AnalysisReportContainerContentTypeEnum = convert_enum_to_graphene_enum(
    AnalysisReportContainer.ContentType, name="AnalysisReportContainerContentTypeEnum"
)


# Client Side Enums

AnalysisReportVariableTypeEnum = convert_enum_to_graphene_enum(ReportEnum.VariableType, name="AnalysisReportVariableTypeEnum")
AnalysisReportTextStyleAlignEnum = convert_enum_to_graphene_enum(
    ReportEnum.TextStyleAlign, name="AnalysisReportTextStyleAlignEnum"
)
AnalysisReportBorderStyleStyleEnum = convert_enum_to_graphene_enum(
    ReportEnum.BorderStyleStyle, name="AnalysisReportBorderStyleStyleEnum"
)
AnalysisReportImageContentStyleFitEnum = convert_enum_to_graphene_enum(
    ReportEnum.ImageContentStyleFit, name="AnalysisReportImageContentStyleFitEnum"
)
AnalysisReportHeadingConfigurationVariantEnum = convert_enum_to_graphene_enum(
    ReportEnum.HeadingConfigurationVariant, name="AnalysisReportHeadingConfigurationVariantEnum"
)
AnalysisReportHorizontalAxisTypeEnum = convert_enum_to_graphene_enum(
    ReportEnum.HorizontalAxisType, name="AnalysisReportHorizontalAxisTypeEnum"
)
AnalysisReportBarChartTypeEnum = convert_enum_to_graphene_enum(ReportEnum.BarChartType, name="AnalysisReportBarChartTypeEnum")
AnalysisReportBarChartDirectionEnum = convert_enum_to_graphene_enum(
    ReportEnum.BarChartDirection, name="AnalysisReportBarChartDirectionEnum"
)
AnalysisReportLegendPositionEnum = convert_enum_to_graphene_enum(
    ReportEnum.LegendPosition, name="AnalysisReportLegendPositionEnum"
)
AnalysisReportLegendDotShapeEnum = convert_enum_to_graphene_enum(
    ReportEnum.LegendDotShape, name="AnalysisReportLegendDotShapeEnum"
)
AnalysisReportAggregationTypeEnum = convert_enum_to_graphene_enum(
    ReportEnum.AggregationType, name="AnalysisReportAggregationTypeEnum"
)
AnalysisReportMapLayerTypeEnum = convert_enum_to_graphene_enum(ReportEnum.MapLayerType, name="AnalysisReportMapLayerTypeEnum")
AnalysisReportScaleTypeEnum = convert_enum_to_graphene_enum(ReportEnum.ScaleType, name="AnalysisReportScaleTypeEnum")
AnalysisReportScalingTechniqueEnum = convert_enum_to_graphene_enum(
    ReportEnum.ScalingTechnique, name="AnalysisReportScalingTechniqueEnum"
)
AnalysisReportLineLayerStrokeTypeEnum = convert_enum_to_graphene_enum(
    ReportEnum.LineLayerStrokeType, name="AnalysisReportLineLayerStrokeTypeEnum"
)

# Model field mapping
enum_map = {
    # Need to pass model with abstract base class
    get_enum_name_from_django_field(field, model_name=model.__name__): enum
    for model, field, enum in (
        (DiscardedEntry, DiscardedEntry.tag, DiscardedEntryTagTypeEnum),
        (TopicModel, TopicModel.status, TopicModelStatusEnum),
        (AutomaticSummary, AutomaticSummary.status, AutomaticSummaryStatusEnum),
        (AnalyticalStatementNGram, AnalyticalStatementNGram.status, AnalyticalStatementNGramStatusEnum),
        (AnalyticalStatementGeoTask, AnalyticalStatementGeoTask.status, AnalyticalStatementGeoTaskStatusEnum),
        (AnalysisReportUpload, AnalysisReportUpload.type, AnalysisReportUploadTypeEnum),
        (AnalysisReportContainer, AnalysisReportContainer.content_type, AnalysisReportContainerContentTypeEnum),
    )
}

# Serializers field mapping
enum_map.update(
    {
        get_enum_name_from_django_field(serializer().fields[field]): enum
        for serializer, field, enum in [
            (AnalysisReportVariableSerializer, "type", AnalysisReportVariableTypeEnum),
            (AnalysisReportTextStyleSerializer, "align", AnalysisReportTextStyleAlignEnum),
            (AnalysisReportBorderStyleSerializer, "style", AnalysisReportBorderStyleStyleEnum),
            (AnalysisReportImageContentStyleSerializer, "fit", AnalysisReportImageContentStyleFitEnum),
            (AnalysisReportHeadingConfigurationSerializer, "variant", AnalysisReportHeadingConfigurationVariantEnum),
            (AnalysisReportHorizontalAxisSerializer, "type", AnalysisReportHorizontalAxisTypeEnum),
            (AnalysisReportBarChartConfigurationSerializer, "type", AnalysisReportBarChartTypeEnum),
            (AnalysisReportBarChartConfigurationSerializer, "direction", AnalysisReportBarChartDirectionEnum),
            (AnalysisReportCategoricalLegendStyleSerializer, "position", AnalysisReportLegendPositionEnum),
            (AnalysisReportCategoricalLegendStyleSerializer, "shape", AnalysisReportLegendDotShapeEnum),
            (AnalysisReportVerticalAxisSerializer, "aggregation_type", AnalysisReportAggregationTypeEnum),
            (AnalysisReportMapLayerConfigurationSerializer, "type", AnalysisReportMapLayerTypeEnum),
            (AnalysisReportSymbolLayerConfigurationSerializer, "scale_type", AnalysisReportScaleTypeEnum),
            (AnalysisReportSymbolLayerConfigurationSerializer, "scaling_technique", AnalysisReportScalingTechniqueEnum),
            (AnalysisReportLineLayerStyleSerializer, "stroke_type", AnalysisReportLineLayerStrokeTypeEnum),
        ]
    }
)
