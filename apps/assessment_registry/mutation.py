import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import AssessmentRegistry
from .schema import AssessmentRegistryType
from .serializers import (
    AssessmentRegistrySerializer
)

AssessmentRegistryCreateInputType = generate_input_type_for_serializer(
    'AssessmentRegistryCreateInputType',
    serializer_class=AssessmentRegistrySerializer
)


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


class Mutation():
    create_assessment_registry = CreateAssessmentRegistry.Field()
    update_assessment_registry = UpdateAssessmentRegistry.Field()
