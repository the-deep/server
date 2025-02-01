import graphene
import requests

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import (
    UnifiedConnector,
    ConnectorSourceLead,
)
from .schema import (
    UnifiedConnectorType,
    ConnectorSourceLeadType,
)
from .serializers import (
    UnifiedConnectorGqSerializer,
    UnifiedConnectorWithSourceGqSerializer,
    ConnectorSourceLeadGqSerializer,
)
from .tasks import process_unified_connector


UnifiedConnectorInputType = generate_input_type_for_serializer(
    'UnifiedConnectorInputType',
    serializer_class=UnifiedConnectorGqSerializer,
)
UnifiedConnectorWithSourceInputType = generate_input_type_for_serializer(
    'UnifiedConnectorWithSourceInputType',
    serializer_class=UnifiedConnectorWithSourceGqSerializer,
)
ConnectorSourceLeadInputType = generate_input_type_for_serializer(
    'ConnectorSourceLeadInputType',
    serializer_class=ConnectorSourceLeadGqSerializer,
)

class KoboValPsGrapheneMutation(PsGrapheneMutation):
    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        from graphql import GraphQLError
        data = kwargs['data']
        print('data is ', data)
        if not cls.validate_kobo(data):
            raise GraphQLError("Invalid Kobo data: 'project_id' and 'token' combination did not retrieve any valid data")
        instance, errors = cls._save_item(data, info, **kwargs)
        return cls(result=instance, errors=errors, ok=not errors)

    @classmethod
    def validate_kobo(cls, data):
        #TODO validate all sources
        sources = data.get('sources', [])
        source = sources[0] if sources else {}
        if source and source.get('title') != 'KoboToolbox':
            return True

        params = source.get("params", {})
        project_id = params.get('project_id')
        token = params.get('token')

        if not project_id or not token:
            return False

        # Validate Kobo API fetch
        return cls.valid_kobo_fetch(project_id, token)

    @classmethod
    def valid_kobo_fetch(cls, project_id, token):
        URL = 'https://kf.kobotoolbox.org/api/v2/assets/'
        api_url = f"{URL}{project_id}/data/?format=json"
        headers = {"Authorization": f"Token {token}"}

        try:
            response = requests.get(api_url, headers=headers, stream=True)
            if response.status_code == 200:
                return True
            else:
                # logger.error("Failed to fetch data from API, Status code: %d", response.status_code)
                return False
        except requests.RequestException as e:
            # logger.critical("A critical error occurred while fetching data: %s", e)
            return False

class UnifiedConnectorMixin():
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(project=info.context.active_project)


class CreateUnifiedConnector(UnifiedConnectorMixin, KoboValPsGrapheneMutation):
    class Arguments:
        data = UnifiedConnectorWithSourceInputType(required=True)
    model = UnifiedConnector
    serializer_class = UnifiedConnectorWithSourceGqSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.CREATE_UNIFIED_CONNECTOR]



class UpdateUnifiedConnector(UnifiedConnectorMixin, KoboValPsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = UnifiedConnectorInputType(required=True)
    model = UnifiedConnector
    serializer_class = UnifiedConnectorGqSerializer
    result = graphene.Field(UnifiedConnectorType)
    permissions = [PP.Permission.UPDATE_UNIFIED_CONNECTOR]




class UpdateUnifiedConnectorWithSource(UnifiedConnectorMixin, KoboValPsGrapheneMutation):
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
        errors = [dict(field='nonFieldErrors', message='Inactive unified connector!!')]
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
        return qs.filter(
            source__unified_connector__project=info.context.active_project
        )


class UnifiedConnectorMutationType(graphene.ObjectType):
    unified_connector_create = CreateUnifiedConnector.Field()
    unified_connector_update = UpdateUnifiedConnector.Field()
    unified_connector_with_source_update = UpdateUnifiedConnectorWithSource.Field()
    unified_connector_delete = DeleteUnifiedConnector.Field()
    unified_connector_trigger = TriggerUnifiedConnector.Field()
    connector_source_lead_update = UpdateConnectorSourceLead.Field()
