import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsBulkGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import Lead, LeadGroup
from .schema import LeadType, LeadGroupType
from .serializers import (
    LeadGqSerializer as LeadSerializer,
)


LeadInputType = generate_input_type_for_serializer(
    'LeadInputType',
    serializer_class=LeadSerializer,
)


class LeadMutationMixin():
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(project=info.context.active_project)


class LeadGroupMutationMixin():
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(project=info.context.active_project)


class CreateLead(LeadMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = LeadInputType(required=True)
    model = Lead
    serializer_class = LeadSerializer
    result = graphene.Field(LeadType)
    permissions = [PP.Permission.CREATE_LEAD]


class UpdateLead(LeadMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = LeadInputType(required=True)
        id = graphene.ID(required=True)
    model = Lead
    serializer_class = LeadSerializer
    result = graphene.Field(LeadType)
    permissions = [PP.Permission.UPDATE_LEAD]


class DeleteLead(LeadMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = Lead
    result = graphene.Field(LeadType)
    permissions = [PP.Permission.DELETE_LEAD]


class DeleteLeadGroup(LeadGroupMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = LeadGroup
    result = graphene.Field(LeadGroupType)
    permissions = [PP.Permission.DELETE_LEAD]


class BulkLeadInputType(LeadInputType):
    id = graphene.ID()


class BulkLead(LeadMutationMixin, PsBulkGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(BulkLeadInputType))

    result = graphene.List(LeadType)
    deleted_result = graphene.List(graphene.NonNull(LeadType))
    # class vars
    model = Lead
    serializer_class = LeadSerializer
    permissions = [PP.Permission.CREATE_LEAD]


class Mutation():
    lead_create = CreateLead.Field()
    lead_update = UpdateLead.Field()
    lead_delete = DeleteLead.Field()
    lead_bulk = BulkLead.Field()
    lead_group_delete = DeleteLeadGroup.Field()
