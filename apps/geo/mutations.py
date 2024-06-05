import graphene

from geo.models import Region, AdminLevel
from geo.schema import RegionType, RegionDetailType, AdminLevelType
from geo.serializers import RegionGqSerializer, AdminLevelGqlSerializer

from utils.graphene.error_types import CustomErrorType
from utils.graphene.mutation import GrapheneMutation, generate_input_type_for_serializer

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
        # instance.save(update_fields=('is_published'))
        return PublishRegion(result=instance, errors=None, ok=True)


class Mutation():
    create_region = CreateRegion.Field()
    create_admin_level = CreateAdminLevel.Field()
    update_admin_level = UpdateAdminLevel.Field()
    publish_region = PublishRegion.Field()
