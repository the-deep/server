from deep.tests import TestCase

from user.models import User
from notification.models import Notification
from project.models import ProjectJoinRequest, Project


class TestNotification(TestCase):
    """Unit test for Notification"""

    def test_notification_created_on_project_join_request(self):
        project = self.create(Project, role=self.admin_role)
        # Create users
        normal_user = self.create(User)
        admin_user = self.create(User)

        # Add admin user to project
        project.add_member(admin_user, role=self.admin_role)
        ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )
        # Get notifications for admin_users
        for user in [self.user, admin_user]:
            notifications = Notification.get_for(user)
            assert notifications.count() == 1,\
                "A notification should have been created for admin"

            notification = notifications[0]
            assert notification.status == Notification.STATUS_UNSEEN
            assert notification.notification_type ==\
                Notification.PROJECT_JOIN_REQUEST
            assert notification.receiver == user
            assert notification.data['status'] == 'pending'

        # Get notifications for requesting user
        # there should be none
        notifications = Notification.get_for(normal_user)
        assert notifications.count() == 0

    def test_notification_updated_on_request_accepted(self):
        project = self.create(Project, role=self.admin_role)
        # Create users
        normal_user = self.create(User)

        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )

        # Get notification for self.user
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 1
        assert notifications[0].notification_type ==\
            Notification.PROJECT_JOIN_REQUEST

        # Update join_request by adding member
        project.add_member(join_request.requested_by, role=join_request.role)

        # Manually updateing join_request because add_member does not trigger
        # receiver for join_request post_save
        join_request.status = 'accepted'
        join_request.role = join_request.role
        join_request.save()

        # Get notifications for admin
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 2
        new_notif = Notification.get_for(self.user).order_by('-timestamp')[0]
        assert new_notif.notification_type ==\
            Notification.PROJECT_JOIN_RESPONSE
        assert new_notif.data['status'] == 'accepted'

        # Get notifications for requesting user
        # He/She should get a notification saying request is accepted
        notifications = Notification.get_for(normal_user)

        assert notifications.count() == 1
        new_notif = notifications[0]
        assert new_notif.notification_type ==\
            Notification.PROJECT_JOIN_RESPONSE
        assert new_notif.data['status'] == 'accepted'

    def test_notification_updated_on_request_rejected(self):
        project = self.create(Project, role=self.admin_role)
        # Create users
        normal_user = self.create(User)

        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )

        # Get notification for self.user
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 1
        assert notifications[0].notification_type ==\
            Notification.PROJECT_JOIN_REQUEST
        assert notifications[0].data['status'] == 'pending'

        # Update join_request without adding member
        join_request.status = 'rejected'
        join_request.role = join_request.role
        join_request.save()

        # Get notifications for admin
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 2
        new_notif = notifications.order_by('-timestamp')[0]
        assert new_notif.notification_type ==\
            Notification.PROJECT_JOIN_RESPONSE
        assert new_notif.data['status'] == 'rejected'

        # Get notifications for requesting user
        # He/She should get a notification saying request is rejected
        notifications = Notification.get_for(normal_user)

        assert notifications.count() == 1
        new_notif = notifications[0]
        assert new_notif.notification_type ==\
            Notification.PROJECT_JOIN_RESPONSE
        assert new_notif.data['status'] == 'rejected'

    def test_notification_updated_on_request_aborted(self):
        project = self.create(Project, role=self.admin_role)
        normal_user = self.create(User)

        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )

        # Get notification for self.user
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 1
        assert notifications[0].notification_type ==\
            Notification.PROJECT_JOIN_REQUEST
        assert notifications[0].data['status'] == 'pending'

        # Now abort join request by deleting it
        join_request.delete()

        # Get notifications again
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 2
        new_notif = notifications.order_by('-timestamp')[0]
        assert new_notif.data['status'] == 'aborted'
        assert new_notif.notification_type ==\
            Notification.PROJECT_JOIN_REQUEST_ABORT

        # Get notifications for requesting user
        # there should be none
        notifications = Notification.get_for(normal_user)
        assert notifications.count() == 0
