import graphene

from deep.permissions import AnalysisFrameworkPermissions as AfP

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation,
    DeleteMutation,
)

from .models import AnalysisFramework
from .serializers import (
    AnalysisFrameworkSerializer,
)
from .schema import AnalysisFrameworkType


AnalysisFrameworkInputType = generate_input_type_for_serializer(
    'AnalysisFrameworkInputType',
    serializer_class=AnalysisFrameworkSerializer
)


class CreateAnalysisFramework(GrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)

    # output fields
    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework
    permissions = []


class UpdateAnalysisFramework(GrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)
        id = graphene.ID(required=True)

    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework
    permissions = [AfP.Permission.CAN_EDIT_FRAMEWORK]


class DeleteAnalysisFramework(DeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)

    # output fields
    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    model = AnalysisFramework
    permissions = [AfP.Permission.DELETE_FRAMEWORK]


class Mutation(object):
    create_analysis_framework = CreateAnalysisFramework.Field()
    update_analysis_framework = UpdateAnalysisFramework.Field()
    delete_analysis_framework = DeleteAnalysisFramework.Field()
