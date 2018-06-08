from project.models import (
    Project,
    ProjectJoinRequest,
)
from project.serializers import ProjectJoinRequestSerializer


class Notification:
    PROJECT_JOIN_REQUEST = 'project_join_request'

    def __init__(self, date, notification_type):
        self.date = date
        self.notification_type = notification_type
        self.details = {}


def _get_project_join_requests(user):
    admin_projects = Project.get_modifiable_for(user)\
        .values_list('id', flat=True)

    join_requests = ProjectJoinRequest.objects.filter(
        project__id__in=admin_projects,
    ).distinct()

    notifications = []
    for request in join_requests:
        date = request.responded_at or request.requested_at
        notification = Notification(
            date=date,
            notification_type=Notification.PROJECT_JOIN_REQUEST,
        )
        notification.details = ProjectJoinRequestSerializer(request).data
        notifications.append(notification)

    return notifications


def generate_notifications(user):
    notifications = []
    notifications += _get_project_join_requests(user)

    notifications = sorted(notifications, key=lambda n: n.date, reverse=True)
    return notifications
