import graphene

from django.utils.translation import gettext

from geo.models import AdminLevel, Region
from geo.schema import AdminLevelType, RegionDetailType
from geo.serializers import AdminLevelGqlSerializer, RegionGqSerializer

from project.models import Project
from utils.graphene.error_types import CustomErrorType
from utils.graphene.mutation import GrapheneMutation, PsDeleteMutation, generate_input_type_for_serializer

from deep.permissions import ProjectPermissions as PP

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


class CreateAdminLevel(GrapheneMutation):
    class Arguments:
        data = AdminLevelInputType(required=True)
    model = AdminLevel
    serializer_class = AdminLevelGqlSerializer
    result = graphene.Field(AdminLevelType)

    @classmethod
    def check_permissions(cls, info, **_):
        return True  # global permission is always true


class RemoveProjectRegion(PsDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)
        projectid = graphene.ID(required=True)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(RegionDetailType)
    permissions = [PP.permission.UPDATE_PROJECT]

    @classmethod
    def check_permissions(cls, info, **_):
        return True

    @staticmethod
    def mutate(root, info, **kwargs):
        project = Project.objects.get(id=kwargs['projectid'])
        region = Region.objects.get(id=kwargs['id'])
        print(project.regions.all())
        if region not in project.regions.all():
            return RemoveProjectRegion(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext(
                        'Region is not associated with Project'
                    ),
                )
            ], ok=False)
        project.regions.remove(region)
        return RemoveProjectRegion(ok=True)


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


class DeleteAdminLevel():
    pass


class Mutation():
    create_region = CreateRegion.Field()
    remove_project_region = RemoveProjectRegion.Field()
    create_admin_level = CreateAdminLevel.Field()
    update_admin_level = UpdateAdminLevel.Field()
