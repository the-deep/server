import django_filters

from deep.filter_set import OrderEnumMixin
from utils.graphene.filters import (
    MultipleInputFilter,
    # IDListFilter,
)

from .models import (
    AssistedTaggingModel,
    AssistedTaggingModelPredictionTag,
)
from .enums import (
    AssistedTaggingModelOrderingEnum,
    AssistedTaggingModelPredictionTagOrderingEnum,
)


# ------------------------------ Graphql filters -----------------------------------
class AssistedTaggingModelGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(AssistedTaggingModelOrderingEnum, method='ordering_filter')

    class Meta:
        model = AssistedTaggingModel
        fields = ()


class AssistedTaggingModelPredictionTagGQFilterSet(OrderEnumMixin, django_filters.FilterSet):
    ordering = MultipleInputFilter(AssistedTaggingModelPredictionTagOrderingEnum, method='ordering_filter')
    is_deprecated = django_filters.BooleanFilter()

    class Meta:
        model = AssistedTaggingModelPredictionTag
        fields = ()
