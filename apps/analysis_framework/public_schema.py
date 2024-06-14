from graphene_django import DjangoObjectType

from utils.graphene.types import CustomDjangoListObjectType

from .filter_set import AnalysisFrameworkGqFilterSet
from .models import AnalysisFramework


class PublicAnalysisFramework(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        skip_registry = True
        fields = ("id", "title")


class PublicAnalysisFrameworkListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFramework
        base_type = PublicAnalysisFramework
        filterset_class = AnalysisFrameworkGqFilterSet
