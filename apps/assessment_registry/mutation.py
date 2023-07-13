import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import AssessmentRegistry, SummaryIssue
from .schema import AssessmentRegistryType, IssueType
from .serializers import (
    AssessmentRegistrySerializer,
    IssueSerializer,
)

AssessmentRegistryCreateInputType = generate_input_type_for_serializer(
    'AssessmentRegistryCreateInputType',
    serializer_class=AssessmentRegistrySerializer
)
IssueCreateInputType = generate_input_type_for_serializer(
    'IssueCreateInputType',
    serializer_class=IssueSerializer
)


class CreateIssue(PsGrapheneMutation):
    class Arguments:
        data = IssueCreateInputType(required=True)

    result = graphene.Field(IssueType)
    serializer_class = IssueSerializer
    model = SummaryIssue
    permissions = []


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
    create_issue = CreateIssue.Field()
