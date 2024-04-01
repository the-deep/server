import graphene
from organization.schema import OrganizationType
from organization.serializers import OrganizationGqSerializer

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation
)

from .models import Organization

OrganizationInputType = generate_input_type_for_serializer(
    'OrganizationInputType',
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
        return True


class Mutation():
    organization_create = OrganizationCreate.Field()
