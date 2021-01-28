from datetime import timedelta

from deep.tests import TestCase
from django.utils import timezone

from user.models import User
from lead.models import Lead
from notification.models import Notification, Assignment
from project.models import ProjectJoinRequest, Project
from entry.models import Entry, EntryComment


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
        assert data['count'] == 0, "Expected zero non-pending notification"

        params.update(dict(is_pending='true'))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 1, "Expected one pending notification"

        # status filter
        params.pop('is_pending', None)
        params.update(dict(status='unseen'))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 1, "One Notification should be with unseen status"

        params.update(dict(status='seen'))
        response = self.client.get(url, params)
        self.assert_200(response)
        data = response.json()
        assert data['count'] == 0, "Zero notification should be with seen status"

        # timestamp filter
        params.pop('status', None)
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

    def test_get_notification_count(self):
        project = self.create_project()
        user = self.create(User)

        url = '/api/v1/notifications/count/'
        data = {'project': project.id}

        self.authenticate()

        response = self.client.get(url, data)
        self.assert_200(response)
        data = response.data
        assert data['total'] == 0
        assert data['unseen_notifications'] == 0
        assert data['unseen_requests'] == 0

        # Now, create join request
        join_request = self.create_join_request(project, user)
        response = self.client.get(url, data)
        data = response.data
        self.assert_200(response)
        assert data['total'] == 1
        assert data['unseen_notifications'] == 0
        assert data['unseen_requests'] == 1

        # Change status of project join request
        join_request.status = 'accepted'
        join_request.responded_by = self.user
        join_request.save()

        response = self.client.get(url, data)
        data = response.data
        self.assert_200(response)
        assert data['total'] == 2
        # One notification is of join request
        # Another new notification is created after user sucessfully joins project
        assert data['unseen_notifications'] == 2
        assert data['unseen_requests'] == 0


class TestAssignmentApi(TestCase):
    """ Api test for assignment model"""

    def test_get_assignments_lead(self):
        project = self.create_project()
        project1 = self.create_project()
        user1 = self.create(User)
        user2 = self.create(User)

        url = '/api/v1/assignments/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        data = response.data
        assert data['count'] == 0, "No Assignments till now"

        # try creating lead
        lead = self.create_lead(project=project, assignee=[user1])
        self.create(Lead, project=project1, assignee=[user2])

        self.authenticate(user1)
        params = {'project': project.id}

        response = self.client.get(url, params)
        self.assert_200(response)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['created_for'], user1.id)
        self.assertEqual(response.data['results'][0]['content_object']['project'], project.id)
        self.assertEqual(response.data['results'][0]['assignment_model_type'], "lead")

    def test_get_assignments_entrycomment(self):
        project = self.create_project()
        project1 = self.create_project()
        entry = self.create(Entry, project=project)
        user1 = self.create(User)
        user2 = self.create(User)

        url = '/api/v1/assignments/'
        entry_comment = self.create(EntryComment, entry=entry, project=project, assignees=[user1])
        self.create(EntryComment, entry=entry, project=project1, assignee=[user2])

        self.authenticate(user1)
        params = {'project': project.id}

        response = self.client.get(url, params)
        self.assert_200(response)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['created_for'], user1.id)
        self.assertEqual(response.data['results'][0]['content_object']['project'], entry.project.id)
        self.assertEqual(response.data['results'][0]['assignment_model_type'], "entrycomment")

    def test_assignment_is_done(self):
        project = self.create(Project)
        user1 = self.create(User)
        user2 = self.create(User)
        assignment = self.create(Assignment, created_for=user1, project=project)
        assignment1 = self.create(Assignment, created_for=user1, project=project)
        assignment2 = self.create(Assignment, created_for=user1, project=project)

        url = '/api/v1/assignments/'
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data['count'], 3)

        # try to put is_done for single assignment
        url = f'/api/v1/assignments/{assignment.id}/'
        data = {
            'is_done': 'true',
        }
        self.authenticate(user1)
        response = self.client.put(url, data)
        self.assert_200(response)
        self.assertEqual(response.data['is_done'], True)

        url = f'/api/v1/assignments/status/'
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data), 2)  # should be to assignemnt that is `is_done=True`
        self.assertEqual(response.data[0]['id'], assignment2.id)
        self.assertEqual(response.data[0]['is_done'], True)
        self.assertEqual(response.data[1]['is_done'], True)
