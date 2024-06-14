import graphene
from organization.schema import OrganizationType
from organization.serializers import OrganizationGqSerializer

from utils.graphene.mutation import GrapheneMutation, generate_input_type_for_serializer

from .models import Organization

OrganizationInputType = generate_input_type_for_serializer(
    "OrganizationInputType",
    serializer_class=OrganizationGqSerializer,
)


class OrganizationCreate(GrapheneMutation):
    class Arguments:
        data = OrganizationInputType(required=True)

    model = Organization
    result = graphene.Field(OrganizationType)
    serializer_class = OrganizationGqSerializer

    @classmethod
    def check_permissions(cls, info, **kwargs):
        return True  # global permission is always True


class Mutation:
    organization_create = OrganizationCreate.Field()
