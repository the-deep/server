from graphene_django import DjangoObjectType

from utils.graphene.types import CustomDjangoListObjectType

from .models import AnalysisFramework
from .filter_set import AnalysisFrameworkGqFilterSet


class PublicAnalysisFramework(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        skip_registry = True
        fields = (
            'id',
            'title'
        )


class PublicAnalysisFrameworkListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFramework
        base_type = PublicAnalysisFramework
        filterset_class = AnalysisFrameworkGqFilterSet
