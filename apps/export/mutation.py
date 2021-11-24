import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)
from deep.permissions import ProjectPermissions as PP
from deep.celery import app as celery_app

from .models import Export
from .schema import UserExportType, get_export_qs
from .serializers import ExportCreateGqlSerializer as ExportCreateSerializer


ExportCreateInputType = generate_input_type_for_serializer(
    'ExportCreateInputType',
    serializer_class=ExportCreateSerializer,
)


class UserExportMutationMixin():
    @classmethod
    def filter_queryset(cls, _, info):
        return get_export_qs(info)


class CreateUserExport(PsGrapheneMutation):
    class Arguments:
        data = ExportCreateInputType(required=True)
    model = Export
    serializer_class = ExportCreateSerializer
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
        export = cls.get_object(info, **kwargs)
        if export.status in [Export.Status.PENDING, Export.Status.STARTED]:
            celery_app.control.revoke(export.get_task_id(clear=True), terminate=True)
            export.status = Export.Status.CANCELED
            export.save(update_fields=('status',))
        return cls(result=export, errors=None, ok=True)


class DeleteUserExport(UserExportMutationMixin, PsGrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = Export
    result = graphene.Field(UserExportType)
    permissions = [PP.Permission.CREATE_EXPORT]

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        export = cls.get_object(info, **kwargs)
        export.is_deleted = True  # Soft delete
        export.save(update_fields=('is_deleted',))
        return cls(result=export, errors=None, ok=True)


class Mutation():
    export_create = CreateUserExport.Field()
    export_cancel = CancelUserExport.Field()
    export_delete = DeleteUserExport.Field()
