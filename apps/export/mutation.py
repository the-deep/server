import graphene

from deep.permissions import ProjectPermissions as PP
from utils.graphene.mutation import (
    GrapheneMutation,
    PsGrapheneMutation,
    generate_input_type_for_serializer,
)

from .models import Export
from .schema import (
    UserExportType,
    UserGenericExportType,
    get_export_qs,
    get_generic_export_qs,
)
from .serializers import (
    UserExportCreateGqlSerializer,
    UserExportUpdateGqlSerializer,
    UserGenericExportCreateGqlSerializer,
)

ExportCreateInputType = generate_input_type_for_serializer(
    "ExportCreateInputType",
    serializer_class=UserExportCreateGqlSerializer,
)


ExportUpdateInputType = generate_input_type_for_serializer(
    "ExportUpdateInputType",
    serializer_class=UserExportUpdateGqlSerializer,
    partial=True,
)


GenericExportCreateInputType = generate_input_type_for_serializer(
    "GenericExportCreateInputType",
    serializer_class=UserGenericExportCreateGqlSerializer,
)


class UserExportMutationMixin:
    @classmethod
    def filter_queryset(cls, _, info):
        return get_export_qs(info)


class UserGenericExportMutationMixin:
    @classmethod
    def filter_queryset(cls, _, info):
        return get_generic_export_qs(info)


class CreateUserExport(PsGrapheneMutation):
    class Arguments:
        data = ExportCreateInputType(required=True)

    model = Export
    serializer_class = UserExportCreateGqlSerializer
    result = graphene.Field(UserExportType)
    permissions = [PP.Permission.CREATE_EXPORT]


class UpdateUserExport(UserExportMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = ExportUpdateInputType(required=True)

    model = Export
    serializer_class = UserExportUpdateGqlSerializer
    result = graphene.Field(UserExportType)
    permissions = [PP.Permission.CREATE_EXPORT]


class CancelUserExport(UserExportMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = Export
    result = graphene.Field(UserExportType)
    permissions = [PP.Permission.CREATE_EXPORT]

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        export, errors = cls.get_object(info, **kwargs)
        if export is None or errors:
            return cls(result=export, errors=errors, ok=True)
        export.cancel()
        return cls(result=export, errors=None, ok=True)


class DeleteUserExport(UserExportMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = Export
    result = graphene.Field(UserExportType)
    permissions = [PP.Permission.CREATE_EXPORT]

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        export, errors = cls.get_object(info, **kwargs)
        if export is None or errors:
            return cls(result=export, errors=errors, ok=True)
        export.cancel(commit=False)
        export.is_deleted = True  # Soft delete
        export.save(
            update_fields=(
                "status",
                "is_deleted",
            )
        )
        return cls(result=export, errors=None, ok=True)


# Generic exports
class CreateUserGenericExport(GrapheneMutation):
    class Arguments:
        data = GenericExportCreateInputType(required=True)

    result = graphene.Field(UserGenericExportType)
    # class vars
    serializer_class = UserGenericExportCreateGqlSerializer
    model = Export

    @classmethod
    def check_permissions(cls, *args, **_):
        return True  # Allow all to create New Exports


class CancelUserGenericExport(UserGenericExportMutationMixin, GrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)

    model = Export
    result = graphene.Field(UserGenericExportType)

    @classmethod
    def check_permissions(cls, *args, **_):
        return True  # Allow all to cancel their exports

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        export, errors = cls.get_object(info, **kwargs)
        if export is None or errors:
            return cls(result=export, errors=errors, ok=True)
        export.cancel()
        return cls(result=export, errors=None, ok=True)


class ProjectMutation:
    export_create = CreateUserExport.Field()
    export_update = UpdateUserExport.Field()
    export_cancel = CancelUserExport.Field()
    export_delete = DeleteUserExport.Field()


class Mutation:
    generic_export_create = CreateUserGenericExport.Field()
    generic_export_cancel = CancelUserGenericExport.Field()
