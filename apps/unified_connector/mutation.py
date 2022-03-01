import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import UnifiedConnector
from .schema import UnifiedConnectorType
from .serializers import (
    UnifiedConnectorGqSerializer as UnifiedConnectorSerializer,
)


UnifiedConnectorInputType = generate_input_type_for_serializer(
    'UnifiedConnectorInputType',
    serializer_class=UnifiedConnectorSerializer,
)


class UnifiedConnectorMixin():
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(project=info.context.active_project)


class CreateUnifiedConnector(UnifiedConnectorMixin, PsGrapheneMutation):
    class Arguments:
        data = UnifiedConnectorInputType(required=True)
    model = UnifiedConnector
    serializer_class = UnifiedConnectorSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.CREATE_UNIFIED_CONNECTOR]


class UpdateUnifiedConnector(UnifiedConnectorMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = UnifiedConnectorInputType(required=True)
    model = UnifiedConnector
    serializer_class = UnifiedConnectorSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.UPDATE_UNIFIED_CONNECTOR]


class DeleteUnifiedConnector(UnifiedConnectorMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = UnifiedConnector
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.DELETE_UNIFIED_CONNECTOR]


class UnifiedConnectorMutationType(graphene.ObjectType):
    unified_connector_create = CreateUnifiedConnector.Field()
    unified_connector_update = UpdateUnifiedConnector.Field()
    unified_connector_delete = DeleteUnifiedConnector.Field()
