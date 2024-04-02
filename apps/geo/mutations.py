import graphene
from geo.models import Region
from geo.schema import RegionType
from geo.serializers import RegionGqSerializer

from deep.permissions import ProjectPermissions as PP
from utils.graphene.mutation import PsGrapheneMutation, generate_input_type_for_serializer

RegionInputType = generate_input_type_for_serializer(
    'RegionInputType',
    serializer_class=RegionGqSerializer,
)


class CreateRegion(PsGrapheneMutation):
    class Arguments:
        data = RegionInputType(required=True)
    model = Region
    serializer_class = RegionGqSerializer
    result = graphene.Field(RegionType)
    permissions = [PP.Permission.UPDATE_PROJECT]


class Mutation():
    create_region = CreateRegion.Field()
