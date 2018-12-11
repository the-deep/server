from deep.tests import TestCase

from user.models import User
from notification.models import Notification
from project.models import ProjectJoinRequest, Project


class TestNotificationAPIs(TestCase):

    def test_get_notifications(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        url = '/api/v1/notifications/'
        data = {'project': project.id}

        self.authenticate()

        response = self.client.get(url, data)
        self.assert_200(response)

        data = response.data
        assert data['count'] == 0, "No notifications so far"

        # Now, create notifications
        self.create_join_request(project, user)

        response = self.client.get(url, data)
        self.assert_200(response)
        data = response.data
        assert data['count'] == 1, "A notification created for join request"
        result = data['results'][0]
        assert 'receiver' in result
        assert 'data' in result
        assert 'project' in result
        assert 'notificationType' in result
        assert 'receiver' in result
        assert 'status' in result
        assert result['status'] == 'unseen'
        # TODO: Check inside data

    def test_update_notification(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        url = '/api/v1/notifications/status/'

        # Create notification
        self.create_join_request(project, user)
        notifs = Notification.get_for(self.user)
        assert notifs.count() == 1
        assert notifs[0].status == Notification.STATUS_UNSEEN

        self.authenticate()

        data = [
            {'id': notifs[0].id, 'status': Notification.STATUS_SEEN}
        ]
        response = self.client.put(url, data)
        self.assert_200(response)

        # Check status
        notif = Notification.objects.get(id=notifs[0].id)
        assert notif.status == Notification.STATUS_SEEN

    def test_update_notification_invalid_data(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        url = '/api/v1/notifications/status/'

        # Create notification
        self.create_join_request(project, user)
        notifs = Notification.get_for(self.user)
        assert notifs.count() == 1
        assert notifs[0].status == Notification.STATUS_UNSEEN

        self.authenticate()

        # Let's send one valid and other invalid data, this should give 400
        data = [
            {
                'id': notifs[0].id + 1,
                'status': Notification.STATUS_SEEN + 'a'
            },
            {
                'id': notifs[0].id,
                'status': Notification.STATUS_SEEN
            },
        ]
        response = self.client.put(url, data)
        self.assert_400(response), "Invalid id and status should give 400"
        data = response.data
        assert 'errors' in data

    def create_join_request(self, project, user=None):
        """Create join_request"""
        user = user or self.create(User)
        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=user,
            role=self.normal_role
        )
        return join_request
