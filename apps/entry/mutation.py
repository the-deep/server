import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
    PsBulkGrapheneMutation,
    PsDeleteMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import Entry
from .schema import EntryType
from .serializers import (
    EntryGqSerializer as EntrySerializer,
)


EntryInputType = generate_input_type_for_serializer(
    'EntryInputType',
    serializer_class=EntrySerializer,
)


class EntryMutationMixin():
    @classmethod
    def filter_queryset(cls, qs, info):
        return qs.filter(
            # Filter by project
            project=info.context.active_project,
            # Filter by project's active analysis_framework (Only show active AF's entries)
            analysis_framework=info.context.active_project.analysis_framework_id,
        )


class CreateEntry(EntryMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = EntryInputType(required=True)
    model = Entry
    serializer_class = EntrySerializer
    result = graphene.Field(EntryType)
    permissions = [PP.Permission.CREATE_ENTRY]


class UpdateEntry(EntryMutationMixin, PsGrapheneMutation):
    class Arguments:
        data = EntryInputType(required=True)
        id = graphene.ID(required=True)
    model = Entry
    serializer_class = EntrySerializer
    result = graphene.Field(EntryType)
    permissions = [PP.Permission.UPDATE_ENTRY]


class DeleteEntry(EntryMutationMixin, PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = Entry
    result = graphene.Field(EntryType)
    permissions = [PP.Permission.DELETE_ENTRY]


class BulkEntryInputType(EntryInputType):
    id = graphene.ID()


class BulkEntry(EntryMutationMixin, PsBulkGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(BulkEntryInputType))
        delete_ids = graphene.List(graphene.NonNull(graphene.ID))

    deleted_result = result = graphene.List(EntryType)
    # class vars
    model = Entry
    serializer_class = EntrySerializer
    permissions = [PP.Permission.CREATE_ENTRY]


class Mutation():
    entry_create = CreateEntry.Field()
    entry_update = UpdateEntry.Field()
    entry_delete = DeleteEntry.Field()
    entry_bulk = BulkEntry.Field()
