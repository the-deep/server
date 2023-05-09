import graphene
from .serializers import (
    AssessmentRegistrySerializer
)
from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from .models import AssessmentRegistry
from .schema import AssessmentRegistryType
from deep.permissions import ProjectPermissions as PP

AssessmentCreateInputType = generate_input_type_for_serializer(
    'AssessmentRegistryCreateInputType',
    serializer_class=AssessmentRegistrySerializer
)


class CreateAssessmentRegistry(PsGrapheneMutation):
    class Arguments:
        data = AssessmentCreateInputType(required=True)

    result = graphene.Field(AssessmentRegistryType)
    serializer_class = AssessmentRegistrySerializer
    model = AssessmentRegistry
    permissions = [PP.Permission.CREATE_ASSESSMENT_REGISTRY]


class Mutation():
    create_assessment_registry = CreateAssessmentRegistry.Field()
