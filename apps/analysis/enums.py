from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import (
    DiscardedEntry,
    TopicModel,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
)

DiscardedEntryTagTypeEnum = convert_enum_to_graphene_enum(DiscardedEntry.TagType, name='DiscardedEntryTagTypeEnum')

TopicModelStatusEnum = convert_enum_to_graphene_enum(TopicModel.Status, name='TopicModelStatusEnum')

AutomaticSummaryStatusEnum = convert_enum_to_graphene_enum(AutomaticSummary.Status, name='AutomaticSummaryStatusEnum')
AnalyticalStatementNGramStatusEnum = convert_enum_to_graphene_enum(
    AnalyticalStatementNGram.Status, name='AnalyticalStatementNGramStatusEnum')
AnalyticalStatementGeoTaskStatusEnum = convert_enum_to_graphene_enum(
    AnalyticalStatementGeoTask.Status, name='AnalyticalStatementGeoTaskStatusEnum')

enum_map = {
    # Need to pass model with abstract base class
    get_enum_name_from_django_field(field, model_name=model.__name__): enum
    for model, field, enum in (
        (DiscardedEntry, DiscardedEntry.tag, DiscardedEntryTagTypeEnum),
        (TopicModel, TopicModel.status, TopicModelStatusEnum),
        (AutomaticSummary, AutomaticSummary.status, AutomaticSummaryStatusEnum),
        (AnalyticalStatementNGram, AnalyticalStatementNGram.status, AnalyticalStatementNGramStatusEnum),
        (AnalyticalStatementGeoTask, AnalyticalStatementGeoTask.status, AnalyticalStatementGeoTaskStatusEnum),
    )
}
