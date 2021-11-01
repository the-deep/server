from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP

from ary.models import Assessment
from ary.filters import AssessmentGQFilterSet


def get_assessment_qs(info):
    assessment_qs = Assessment.objects.filter(project=info.context.active_project)
    if PP.check_permission(info, PP.Permission.VIEW_ENTRY):
        return assessment_qs
    return Assessment.objects.none()


class AssessmentType(DjangoObjectType):
    class Meta:
        model = Assessment
        fields = (
            'id', 'lead', 'project', 'lead_group',
            'metadata', 'methodology', 'summary',
            'score', 'questionnaire',
        )

    @staticmethod
    def get_custom_queryset(queryset, info, **kwargs):
        return get_assessment_qs(info)


class AssessmentListType(CustomDjangoListObjectType):
    class Meta:
        model = Assessment
        filterset_class = AssessmentGQFilterSet


class Query:
    assessment = DjangoObjectField(AssessmentType)
    assessments = DjangoPaginatedListObjectField(
        AssessmentListType,
        pagination=PageGraphqlPagination(
            page_size_query_param='pageSize'
        )
    )

    @staticmethod
    def resolve_assessments(root, info, **kwargs) -> QuerySet:
        return get_assessment_qs(info)
