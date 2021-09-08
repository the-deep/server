import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from django.core.exceptions import PermissionDenied

from deep.permissions import AnalysisFrameworkPermissions as AfP

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation,
    AfGrapheneMutation,
    AfBulkGrapheneMutation,
)

from .models import (
    AnalysisFramework,
    AnalysisFrameworkMembership,
)
from .serializers import (
    AnalysisFrameworkGqlSerializer as AnalysisFrameworkSerializer,
    AnalysisFrameworkMembershipGqlSerializer as AnalysisFrameworkMembershipSerializer,
)
from .schema import (
    AnalysisFrameworkDetailType,
    AnalysisFrameworkMembershipType,
)


AnalysisFrameworkInputType = generate_input_type_for_serializer(
    'AnalysisFrameworkInputType',
    serializer_class=AnalysisFrameworkSerializer
)

AnalysisFrameworkMembershipInputType = generate_input_type_for_serializer(
    'AnalysisFrameworkMembershipInputType',
    serializer_class=AnalysisFrameworkMembershipSerializer
)


class CreateAnalysisFramework(GrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)

    # output fields
    result = graphene.Field(AnalysisFrameworkDetailType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework

    @classmethod
    def check_permissions(cls, *args, **_):
        return True  # Allow all to create AF


class UpdateAnalysisFramework(AfGrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)

    result = graphene.Field(AnalysisFrameworkDetailType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework
    permissions = [AfP.Permission.CAN_EDIT_FRAMEWORK]

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        kwargs['id'] = info.context.active_af.id
        return super().perform_mutate(root, info, **kwargs)


class BulkAnalysisFrameworkMembershipInputType(AnalysisFrameworkMembershipInputType):
    id = graphene.ID()


class BulkUpdateAnalysisFrameworkMembership(AfBulkGrapheneMutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(BulkAnalysisFrameworkMembershipInputType), required=True)
        delete_ids = graphene.List(graphene.NonNull(graphene.ID))

    deleted_result = result = graphene.List(AnalysisFrameworkMembershipType)
    # class vars
    serializer_class = AnalysisFrameworkMembershipSerializer
    model = AnalysisFrameworkMembership
    permissions = [AfP.Permission.CAN_ADD_USER]

    @classmethod
    def get_valid_delete_items(cls, info, delete_ids):
        af = info.context.active_af
        return AnalysisFrameworkMembership.objects.filter(
            pk__in=delete_ids,  # id's provided
            framework=af,  # For active AF
        ).exclude(
            # Exclude yourself and owner of the AF
            member__in=[info.context.user, af.created_by]
        )


class AnalysisFrameworkMutationType(DjangoObjectType):
    """
    This mutation is for other scoped objects
    """
    analysis_framework_update = UpdateAnalysisFramework.Field()
    analysis_framework_membership_bulk = BulkUpdateAnalysisFrameworkMembership.Field()

    class Meta:
        model = AnalysisFramework
        skip_registry = True
        fields = ('id', 'title')

    @staticmethod
    def get_custom_node(_, info, id):
        try:
            af = AnalysisFramework.get_for_gq(info.context.user, only_member=True).get(pk=id)
            info.context.set_active_af(af)
            return af
        except AnalysisFramework.DoesNotExist:
            raise PermissionDenied()


class Mutation(object):
    analysis_framework_create = CreateAnalysisFramework.Field()
    analysis_framework = DjangoObjectField(AnalysisFrameworkMutationType)
