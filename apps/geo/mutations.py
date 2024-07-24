import graphene
from django.utils.translation import gettext

from geo.models import Region, AdminLevel
from geo.schema import RegionType, RegionDetailType, AdminLevelType
from geo.serializers import RegionGqSerializer, AdminLevelGqlSerializer

from utils.graphene.error_types import CustomErrorType
from utils.graphene.mutation import DeleteMutation, GrapheneMutation, generate_input_type_for_serializer

RegionInputType = generate_input_type_for_serializer(
    'RegionInputType',
    serializer_class=RegionGqSerializer,
)

AdminLevelInputType = generate_input_type_for_serializer(
    'AdminLevelInputType',
    serializer_class=AdminLevelGqlSerializer,
)


class CreateRegion(GrapheneMutation):
    class Arguments:
        data = RegionInputType(required=True)
    model = Region
    serializer_class = RegionGqSerializer
    result = graphene.Field(RegionDetailType)

    @classmethod
    def check_permissions(cls, info, **_):
        return True  # global permission is always true
    #  NOTE: Region permission is checked using serializers


class CreateAdminLevel(GrapheneMutation):
    class Arguments:
        data = AdminLevelInputType(required=True)
    model = AdminLevel
    serializer_class = AdminLevelGqlSerializer
    result = graphene.Field(AdminLevelType)

    @classmethod
    def check_permissions(cls, info, **_):
        return True  # global permission is always true
    #  NOTE: Region permission is checked using serializers


class UpdateAdminLevel(GrapheneMutation):
    class Arguments:
        data = AdminLevelInputType(required=True)
        id = graphene.ID(required=True)
    model = AdminLevel
    serializer_class = AdminLevelGqlSerializer
    result = graphene.Field(AdminLevelType)

    @classmethod
    def check_permissions(cls, info, **_):
        return True  # global permission is always True


class DeleteAdminLevel(DeleteMutation):
    class Arguments:
        admin_level_id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(AdminLevelType)

    @staticmethod
    def mutate(root, info, admin_level_id):
        admin_level_qs = AdminLevel.objects.filter(
            id=admin_level_id,
            region__is_published=False
        )
        if not admin_level_qs:
            return DeleteAdminLevel(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext(
                        'You should be Region owner to delete admin level or region is published'
                    ),
                )
            ], ok=False)
        admin_level_qs.delete()
        return DeleteAdminLevel(result=admin_level_qs, errors=None, ok=True)


class PublishRegion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = Region
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(RegionType)

    @staticmethod
    def mutate(root, info, id):
        try:
            instance = Region.objects.get(
                created_by=info.context.user,
                id=id
            )
        except Region.DoesNotExist:
            return PublishRegion(errors=[
                dict(
                    field='nonFieldErrors',
                    messages="Authorized User can only published the region"
                )
            ], ok=False)
        instance.is_published = True
        instance.save(update_fields=['is_published'])
        return PublishRegion(result=instance, errors=None, ok=True)


class Mutation():
    create_region = CreateRegion.Field()
    create_admin_level = CreateAdminLevel.Field()
    publish_region = PublishRegion.Field()
    create_admin_level = CreateAdminLevel.Field()
    update_admin_level = UpdateAdminLevel.Field()
    delete_admin_level = DeleteAdminLevel.Field()
