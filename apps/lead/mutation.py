import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation,
    DeleteMutation,
)

from .models import Lead
from .schema import LeadType
from .serializers import LeadGqSerializer as LeadSerializer


LeadInputType = generate_input_type_for_serializer(
    'LeadInputType',
    serializer_class=LeadSerializer,
)


class CreateLead(GrapheneMutation):
    class Arguments:
        data = LeadInputType(required=True)
    model = Lead
    serializer_class = LeadSerializer
    result = graphene.Field(LeadType)
    permission_classes = []  # TODO: Add permission check and test


class UpdateLead(GrapheneMutation):
    class Arguments:
        data = LeadInputType(required=True)
        id = graphene.ID(required=True)
    model = Lead
    serializer_class = LeadSerializer
    result = graphene.Field(LeadType)


class DeleteLead(DeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = Lead
    result = graphene.Field(LeadType)


class Mutation():
    create_lead = CreateLead.Field()
    update_lead = UpdateLead.Field()
    delete_lead = DeleteLead.Field()
