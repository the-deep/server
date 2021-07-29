import graphene
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination
from django.db.models import QuerySet

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField

from .models import (
    AnalysisFramework,
    Section,
    Widget,
)


class WidgetType(DjangoObjectType):
    class Meta:
        model = Widget
        fields = ('id', 'key', 'title', 'widget_id', 'order', 'properties')


class SectionType(DjangoObjectType):
    widgets = DjangoListField(WidgetType)

    class Meta:
        model = Section
        fields = ('id', 'title', 'order',)

    @staticmethod
    def resolve_widgets(root, info):
        return info.context.dl.analysis_framework.sections_widgets.load(root.id)


class AnalysisFrameworkType(DjangoObjectType):
    class Meta:
        model = AnalysisFramework
        only_fields = ('id', 'title', 'description', 'is_private')

    current_user_role = graphene.String()

    @staticmethod
    def get_custom_node(_, info, id):
        try:
            af = AnalysisFramework.get_for_gq(info.context.user).get(pk=id)
            info.context.set_active_af(af)
            return af
        except AnalysisFramework.DoesNotExist:
            return None


class AnalysisFrameworkDetailType(AnalysisFrameworkType):
    primary_tagging = DjangoListField(SectionType)  # With section
    secondary_tagging = DjangoListField(WidgetType)  # Without section

    class Meta:
        model = AnalysisFramework
        skip_registry = True
        only_fields = ('id', 'title', 'description', 'is_private')

    @staticmethod
    def resolve_primary_tagging(root, info):
        return info.context.dl.analysis_framework.sections.load(root.id)

    @staticmethod
    def resolve_secondary_tagging(root, info):
        return info.context.dl.analysis_framework.secondary_widgets.load(root.id)


class AnalysisFrameworkListType(CustomDjangoListObjectType):
    class Meta:
        model = AnalysisFramework
        filter_fields = ['id']


class Query:
    analysis_framework = DjangoObjectField(AnalysisFrameworkDetailType)
    analysis_frameworks = DjangoPaginatedListObjectField(
        AnalysisFrameworkListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_analysis_frameworks(root, info, **kwargs) -> QuerySet:
        return AnalysisFramework.get_for_gq(info.context.user).distinct()
