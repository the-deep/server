import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    GrapheneMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import AssessmentRegistry, SummaryIssue
from .schema import AssessmentRegistryType, AssessmentRegistrySummaryIssueType
from .serializers import (
    AssessmentRegistrySerializer,
    IssueSerializer,
)

AssessmentRegistryCreateInputType = generate_input_type_for_serializer(
    'AssessmentRegistryCreateInputType',
    serializer_class=AssessmentRegistrySerializer
)
AssessmentRegistrySummaryIssueCreateInputType = generate_input_type_for_serializer(
    'AssessmentRegistrySummaryIssueCreateInputType',
    serializer_class=IssueSerializer
)


class AssessmentRegistryCreateIssue(GrapheneMutation):
    class Arguments:
        data = AssessmentRegistrySummaryIssueCreateInputType()

    result = graphene.Field(AssessmentRegistrySummaryIssueType)
    serializer_class = IssueSerializer
    model = SummaryIssue

    @classmethod
    def check_permissions(cls, *args, **_):
        return True  # Allow all to create New Issue


class CreateAssessmentRegistry(PsGrapheneMutation):
    class Arguments:
        data = AssessmentRegistryCreateInputType(required=True)

    result = graphene.Field(AssessmentRegistryType)
    serializer_class = AssessmentRegistrySerializer
    model = AssessmentRegistry
    permissions = [PP.Permission.CREATE_ASSESSMENT_REGISTRY]


class UpdateAssessmentRegistry(PsGrapheneMutation):
    class Arguments:
        data = AssessmentRegistryCreateInputType(required=True)
        id = graphene.ID(required=False)

    result = graphene.Field(AssessmentRegistryType)
    serializer_class = AssessmentRegistrySerializer
    model = AssessmentRegistry
    permissions = [PP.Permission.UPDATE_ASSESSMENT_REGISTRY]


class ProjectMutation():
    create_assessment_registry = CreateAssessmentRegistry.Field()
    update_assessment_registry = UpdateAssessmentRegistry.Field()


class Mutation():
    create_assessment_reg_summary_issue = AssessmentRegistryCreateIssue.Field()
