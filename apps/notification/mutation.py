from django.utils.translation import gettext

import graphene

from utils.graphene.mutation import generate_input_type_for_serializer
from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType

from .serializers import NotificationGqSerializer
from .schema import NotificationType
from .models import Notification

NotificationStatusInputType = generate_input_type_for_serializer(
    'NotificationStatusInputType',
    serializer_class=NotificationGqSerializer

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


class Mutation(object):
    notification_status_update = NotificationStatusUpdate.Field()
