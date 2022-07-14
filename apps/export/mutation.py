import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from deep.permissions import ProjectPermissions as PP

from .models import Export
from .schema import UserExportType, get_export_qs
from .serializers import UserExportCreateGqlSerializer, UserExportUpdateGqlSerializer


ExportCreateInputType = generate_input_type_for_serializer(
    'ExportCreateInputType',
    serializer_class=UserExportCreateGqlSerializer,
)


ExportUpdateInputType = generate_input_type_for_serializer(
    'ExportUpdateInputType',
    serializer_class=UserExportUpdateGqlSerializer,
    partial=True,
)


class UserExportMutationMixin():
    @classmethod
    def filter_queryset(cls, _, info):
        return get_export_qs(info)


class CreateUserExport(PsGrapheneMutation):
    class Arguments:
        data = ExportCreateInputType(required=True)
    model = Export
    serializer_class = UserExportCreateGqlSerializer
    result = graphene.Field(UserExportType)
    permissions = [PP.Permission.CREATE_EXPORT]


class UpdateUserExport(UserExportMutationMixin, PsGrapheneMutation):
    class Arguments:
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
        export.cancle()
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
        export.cancle(commit=False)
        export.is_deleted = True  # Soft delete
        export.save(update_fields=('status', 'is_deleted',))
        return cls(result=export, errors=None, ok=True)


class Mutation():
    export_create = CreateUserExport.Field()
    export_update = UpdateUserExport.Field()
    export_cancel = CancelUserExport.Field()
    export_delete = DeleteUserExport.Field()
