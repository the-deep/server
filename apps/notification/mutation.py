from django.utils.translation import gettext

import graphene

from utils.graphene.mutation import GrapheneMutation, PsGrapheneMutation, generate_input_type_for_serializer
from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType

from .serializers import AssignmentSerializer, NotificationGqSerializer
from .schema import AssignmentType, NotificationType
from .models import Assignment, Notification

NotificationStatusInputType = generate_input_type_for_serializer(
    'NotificationStatusInputType',
    serializer_class=NotificationGqSerializer

)

AssignmentInputType = generate_input_type_for_serializer(
    'AssignmentInputType',
    serializer_class=AssignmentSerializer
)


class NotificationStatusUpdate(graphene.Mutation):
    class Arguments:
        data = NotificationStatusInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(NotificationType)

    @staticmethod
    def mutate(root, info, data):
        try:
            instance = Notification.objects.get(id=data['id'], receiver=info.context.request.user)

        except Notification.DoesNotExist:
            return NotificationStatusUpdate(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext('Notification doesnot exist')
                )
            ], ok=False)
        serializer = NotificationGqSerializer(instance=instance, data=data,
                                              context={'request': info.context.request}, partial=True)
        if errors := mutation_is_not_valid(serializer):
            return NotificationStatusUpdate(errors=errors, ok=False)
        instance = serializer.save()
        return NotificationStatusUpdate(result=instance, ok=True, errors=None)


class AssignmentStatusUpdate(GrapheneMutation):
    class Arguments:
        id = graphene.ID(required=True)
        data = AssignmentInputType(required=True)
    model = Assignment
    result = graphene.Field(AssignmentType)
    serializer_class = AssignmentSerializer
    permissions = []

    @classmethod
    def check_permissions(cls, info, **kwargs):
        return True  # global permissions is always True


class AsssignmentBulkStatusUpdate(PsGrapheneMutation):
    class Arguments:
        is_done = graphene.Boolean(required=True)
    model = Assignment
    result = graphene.List(graphene.NonNull(AssignmentType))
    permissions = []

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        instance = cls.model.objects.filter(created_for=info.context.user, is_done=False)
        instance.update(is_done=kwargs['is_done'])
        return cls(result=instance, ok=True)


class Mutation(object):
    notification_status_update = NotificationStatusUpdate.Field()
    assignment_status_update = AssignmentStatusUpdate.Field()
    assignment_bulk_status_update = AsssignmentBulkStatusUpdate.Field()
