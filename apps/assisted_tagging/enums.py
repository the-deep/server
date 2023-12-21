import graphene

from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
    get_enum_name_from_django_field,
)

from .models import (
    DraftEntry,
    AssistedTaggingPrediction,
)

DraftEntryPredictionStatusEnum = convert_enum_to_graphene_enum(
    DraftEntry.PredictionStatus, name='DraftEntryPredictionStatusEnum')
AssistedTaggingPredictionDataTypeEnum = convert_enum_to_graphene_enum(
    AssistedTaggingPrediction.DataType, name='AssistedTaggingPredictionDataTypeEnum')
DraftEntryTypeEnum = convert_enum_to_graphene_enum(
    DraftEntry.Type, name="DraftEntryTypeEnum"
)

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (DraftEntry.prediction_status, DraftEntryPredictionStatusEnum),
        (AssistedTaggingPrediction.data_type, AssistedTaggingPredictionDataTypeEnum),
        (DraftEntry.type, DraftEntryTypeEnum),
    )
}


class AssistedTaggingModelOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    # DESC
    DESC_ID = f'-{ASC_ID}'


class AssistedTaggingModelPredictionTagOrderingEnum(graphene.Enum):
    # ASC
    ASC_ID = 'id'
    # DESC
    DESC_ID = f'-{ASC_ID}'
