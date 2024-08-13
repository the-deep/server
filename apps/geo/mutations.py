import graphene

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
    #  NOTE: Project permission is checked using serializers


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


class UpdateRegion(GrapheneMutation):
    class Arguments:
        data = RegionInputType(required=True)
        id = graphene.ID(required=True)
    model = Region
    serializer_class = RegionGqSerializer
    result = graphene.Field(RegionDetailType)

    @classmethod
    def check_permissions(cls, info, **_):
        return True  # global permission is always true


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
        admin_level = AdminLevel.objects.filter(
            id=admin_level_id,
        ).first()

        error_data = []
        if admin_level is None:
            error_data.append("AdminLevel doesn't exist")
        elif admin_level.region.created_by_id != info.context.user.id:
            error_data.append("Only region owner can delete admin level")
        elif admin_level.region.is_published:
            error_data.append("Published region can't be changed. Please contact system admin")
        if error_data:
            return DeleteAdminLevel(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=error_data
                )
            ], ok=False)
        admin_level.delete()
        return DeleteAdminLevel(errors=None, ok=True)


class PublishRegion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    model = Region
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(RegionType)

    @staticmethod
    def mutate(root, info, id):
        instance = Region.objects.filter(
            id=id
        ).first()

        error_data = []
        if instance is None:
            error_data.append('Region does\'t exist')
        elif instance.created_by != info.context.user:
            error_data.append('Authorized User can only published the region')
        if error_data:
            return PublishRegion(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=error_data
                )
            ], ok=False)

        instance.is_published = True
        instance.save(update_fields=['is_published'])
        return PublishRegion(result=instance, errors=None, ok=True)


class Mutation():
    create_region = CreateRegion.Field()
    update_region = UpdateRegion.Field()
    create_admin_level = CreateAdminLevel.Field()
    publish_region = PublishRegion.Field()
    update_admin_level = UpdateAdminLevel.Field()
    delete_admin_level = DeleteAdminLevel.Field()
