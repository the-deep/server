import graphene
from ary.models import Assessment
from ary.schema import AssessmentType

from deep.permissions import ProjectPermissions as PP
from utils.graphene.mutation import PsDeleteMutation


class AssessmentMutationMixin:
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(project=info.context.active_project)


class DeleteAssessment(AssessmentMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = Assessment
    result = graphene.Field(AssessmentType)
    permissions = [PP.Permission.DELETE_LEAD]


class Mutation:
    assessment_delete = DeleteAssessment.Field()
