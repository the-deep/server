import graphene

from geo.models import Region
from geo.schema import RegionType
from geo.serializers import RegionGqSerializer

from utils.graphene.mutation import GrapheneMutation, generate_input_type_for_serializer

RegionInputType = generate_input_type_for_serializer(
    'RegionInputType',
    serializer_class=RegionGqSerializer,
)


class CreateRegion(GrapheneMutation):
    class Arguments:
        data = RegionInputType(required=True)
    model = Region
    serializer_class = RegionGqSerializer
    result = graphene.Field(RegionType)

    @classmethod
    def check_permissions(cls, info, **_):
        return True  # global permission is always true


class Mutation():
    create_region = CreateRegion.Field()
