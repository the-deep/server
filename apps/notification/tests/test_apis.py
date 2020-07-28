from datetime import timedelta

from deep.tests import TestCase
from django.utils import timezone

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
        data = response.json()
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

    def test_get_filtered_notifications(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)
        url = '/api/v1/notifications/'
        params = {'project': project.id}

        self.authenticate()
        # store the time
        before = timezone.now()
        # create a notification
        self.create_join_request(project, user)

        # filtering of timestamp has a step of ONE DAY
        after = before + timedelta(days=1)

        print(before.strftime('%Y-%m-%d%z'))
        print(after.strftime('%Y-%m-%d%z'))

        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 1, "A notification was created for join request but didnot show"

        # now applying filters

        # is_pending filter
        # by default the notification created is in status = pending
        params.update(dict(is_pending='false'))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 0, "One Notification was in pending"

        params.update(dict(is_pending='true'))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 1, "One Notification was in pending"

        # timestamp filter
        params.pop('is_pending', None)
        params.update(dict(timestamp__gt=before.strftime('%Y-%m-%d%z')))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 1, "One Notification should be after 'before time' "

        params.pop('timestamp__gt', None)
        params.update(dict(timestamp__lt=before.strftime('%Y-%m-%d%z')))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 0, "No notification should be before 'before time'"

        params.pop('timestamp__lt', None)
        params.update(dict(timestamp__gt=after.strftime('%Y-%m-%d%z')))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 0, "No notification should be after 'after time'"

        params.update(dict(timestamp__gt=before.strftime('%Y-%m-%d%z'),
                           timestamp__lt=after.strftime('%Y-%m-%d%z')))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 1, "One notification should be after 'before time' and before 'after time'"
