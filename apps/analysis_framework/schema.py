from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from analysis_framework.models import (
    AnalysisFramework,
    Widget,
)
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField


class WidgetType(DjangoObjectType):
    class Meta:
        model = Widget


class WidgetListType(CustomDjangoListObjectType):
    class Meta:
        model = Widget
        filter_fields = ['id']


class AnalysisFrameworkType(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        only_fields = ('title', 'widgets', 'description', 'is_private')


class AnalysisFrameworkListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFramework
        filter_fields = ['id']

    widget_set = DjangoPaginatedListObjectField(WidgetListType)


class Query:
    analysis_framework = DjangoObjectField(AnalysisFrameworkType)
    analysis_framework_list = DjangoPaginatedListObjectField(
        AnalysisFrameworkListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )
