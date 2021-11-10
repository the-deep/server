from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField, PageGraphqlPagination

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from deep.permissions import ProjectPermissions as PP
from user_resource.schema import UserResourceMixin

from lead.models import Lead
from ary.models import Assessment
from ary.filters import AssessmentGQFilterSet


def get_assessment_qs(info):
    assessment_qs = Assessment.objects.filter(project=info.context.active_project)
    # Generate querset according to permission
    if PP.check_permission(info, PP.Permission.VIEW_ALL_LEAD):
        return assessment_qs
    elif PP.check_permission(info, PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD):
        return assessment_qs.filter(lead__confidentiality=Lead.Confidentiality.UNPROTECTED)
    return Assessment.objects.none()


class AssessmentType(UserResourceMixin, DjangoObjectType):
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
