import graphene

from geo.models import AdminLevel, Region
from geo.schema import AdminLevelType, RegionDetailType
from geo.serializers import AdminLevelGqlSerializer, RegionGqSerializer

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


class PublishRegion(GrapheneMutation):
    class Arguments:
        data = RegionPublishInputType(required=True)
        id = graphene.ID(required=True)
    model = Region
    serializer_class = PublishRegionGqSerializer
    result = graphene.Field(RegionType)

    @classmethod
    def check_permissions(cls, *args, **_):
        if PP.Permission.UPDATE_PROJECT:
            return True


class Mutation():
    create_region = CreateRegion.Field()
    create_admin_level = CreateAdminLevel.Field()
    update_admin_level = UpdateAdminLevel.Field()
    publish_region = PublishRegion.Field()
