import graphene

from deep.permissions import ProjectPermissions as PP
from utils.graphene.mutation import (
    PsDeleteMutation,
    PsGrapheneMutation,
    generate_input_type_for_serializer,
)

from .models import ConnectorSourceLead, UnifiedConnector
from .schema import ConnectorSourceLeadType, UnifiedConnectorType
from .serializers import (
    ConnectorSourceLeadGqSerializer,
    UnifiedConnectorGqSerializer,
    UnifiedConnectorWithSourceGqSerializer,
)
from .tasks import process_unified_connector

UnifiedConnectorInputType = generate_input_type_for_serializer(
    "UnifiedConnectorInputType",
    serializer_class=UnifiedConnectorGqSerializer,
)
UnifiedConnectorWithSourceInputType = generate_input_type_for_serializer(
    "UnifiedConnectorWithSourceInputType",
    serializer_class=UnifiedConnectorWithSourceGqSerializer,
)
ConnectorSourceLeadInputType = generate_input_type_for_serializer(
    "ConnectorSourceLeadInputType",
    serializer_class=ConnectorSourceLeadGqSerializer,
)


class UnifiedConnectorMixin:
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(project=info.context.active_project)


class CreateUnifiedConnector(UnifiedConnectorMixin, PsGrapheneMutation):
    class Arguments:
        data = UnifiedConnectorWithSourceInputType(required=True)

    model = UnifiedConnector
    serializer_class = UnifiedConnectorWithSourceGqSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.CREATE_UNIFIED_CONNECTOR]


class UpdateUnifiedConnector(UnifiedConnectorMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = UnifiedConnectorInputType(required=True)

    model = UnifiedConnector
    serializer_class = UnifiedConnectorGqSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.UPDATE_UNIFIED_CONNECTOR]


class UpdateUnifiedConnectorWithSource(UnifiedConnectorMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = UnifiedConnectorWithSourceInputType(required=True)

    model = UnifiedConnector
    serializer_class = UnifiedConnectorWithSourceGqSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.UPDATE_UNIFIED_CONNECTOR]


class DeleteUnifiedConnector(UnifiedConnectorMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = UnifiedConnector
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.DELETE_UNIFIED_CONNECTOR]


class TriggerUnifiedConnector(UnifiedConnectorMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = UnifiedConnector
    serializer_class = UnifiedConnectorGqSerializer
    permissions = [PP.Permission.VIEW_UNIFIED_CONNECTOR]

    @classmethod
    def perform_mutate(cls, _, info, **kwargs):
        instance, errors = cls.get_object(info, **kwargs)
        if errors:
            return cls(errors=errors, ok=False)
        if instance.is_active:
            process_unified_connector.delay(instance.pk)
            return cls(errors=None, ok=True)
        errors = [dict(field="nonFieldErrors", message="Inactive unified connector!!")]
        return cls(errors=errors, ok=False)


class UpdateConnectorSourceLead(PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = ConnectorSourceLeadInputType(required=True)

    model = ConnectorSourceLead
    serializer_class = ConnectorSourceLeadGqSerializer
    permissions = [PP.Permission.VIEW_UNIFIED_CONNECTOR]
    result = graphene.Field(ConnectorSourceLeadType)

    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(source__unified_connector__project=info.context.active_project)


class UnifiedConnectorMutationType(graphene.ObjectType):
    unified_connector_create = CreateUnifiedConnector.Field()
    unified_connector_update = UpdateUnifiedConnector.Field()
    unified_connector_with_source_update = UpdateUnifiedConnectorWithSource.Field()
    unified_connector_delete = DeleteUnifiedConnector.Field()
    unified_connector_trigger = TriggerUnifiedConnector.Field()
    connector_source_lead_update = UpdateConnectorSourceLead.Field()
