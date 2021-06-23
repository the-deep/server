from unittest.mock import patch

from deep.tests import TestCase
from user.models import User
from notification.models import Notification, Assignment
from project.models import ProjectJoinRequest, Project
from lead.models import Lead
from entry.models import EntryComment


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
            role=self.normal_role,
            data={'reason': 'bla'}
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
            assert notification.data['data']['reason'] is not None

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
            role=self.normal_role,
            data={'reason': 'bla'}
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
            role=self.normal_role,
            data={'reason': 'bla'}
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
            role=self.normal_role,
            data={'reason': 'bla'}
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


class TestAssignment(TestCase):
    """ Unit test for Assignment"""

    @patch('notification.receivers.entry_comment.get_current_user')
    def test_create_assignment_create_on_entry_comment(self, get_user_mocked_func):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        get_user_mocked_func.return_value = user2

        old_assignment_count = Assignment.objects.count()
        entry_comment = self.create(EntryComment, entry=entry)
        new_assignment_count = Assignment.objects.count()

        self.assertEqual(old_assignment_count, new_assignment_count)

        entry_comment.assignees.add(user1)
        new_assignment_count = Assignment.objects.count()
        self.assertEqual(old_assignment_count + 1, new_assignment_count)

        # try to change the assigne for the entry_comment and test for the change in assignment
        entry_comment.assignees.remove(user1)
        entry_comment.assignees.add(user2)
        self.assertEqual(old_assignment_count + 1, new_assignment_count)
        assignment = Assignment.objects.get(entry_comment__id=entry_comment.id)
        self.assertEqual(assignment.created_for, user2)  # should represent the new user2

        # try to add another user and remove both from assignee
        entry_comment.assignees.add(user1)
        new_assignment_count = Assignment.objects.count()
        self.assertEqual(old_assignment_count + 2, new_assignment_count)

        # try to get the assignment for user
        entry_comment.assignees.add(user1, user2)
        assignment = Assignment.get_for(user1)
        assert assignment.count() == 1  # for only the user
        assert get_user_mocked_func.called

    @patch('notification.receivers.entry_comment.get_current_user')
    def test_assignment_create_on_lead_create(self, get_user_mocked_func):
        project = self.create(Project)
        user1 = self.create_user()
        user2 = self.create_user()
        get_user_mocked_func.return_value = user2

        old_assignment_count = Assignment.objects.count()
        lead = self.create(Lead, project=project)
        new_assignment_count = Assignment.objects.count()
        self.assertEqual(old_assignment_count, new_assignment_count)  # no assignment to be cretaed for empyt assignee

        # try add assignee in the lead
        lead.assignee.add(user1)
        new_assignment_count = Assignment.objects.count()
        self.assertEqual(old_assignment_count + 1, new_assignment_count)

        # try to change the assigne for the lead and test for the change in assignment
        lead.assignee.remove(user1)
        lead.assignee.add(user2)
        self.assertEqual(old_assignment_count + 1, new_assignment_count)
        assignment = Assignment.objects.get(lead__id=lead.id)
        self.assertEqual(assignment.created_for, user2)  # should represent the new user2

        # try to add another user and remove both from assignee
        lead.assignee.add(user1)
        new_assignment_count = Assignment.objects.count()
        self.assertEqual(old_assignment_count + 2, new_assignment_count)

        lead.assignee.remove(user1, user2)
        self.assertEqual(Assignment.objects.count(), 0)

        # try to get the assignment for user
        lead.assignee.add(user1, user2)
        assignment = Assignment.get_for(user1)
        assert assignment.count() == 1  # for only the user
        assert get_user_mocked_func.called

    @patch('notification.receivers.entry_comment.get_current_user')
    def test_assignment_on_lead_and_entry_comment_delete(self, get_user_mocked_func):
        project = self.create_project()
        user1 = self.create(User)
        user2 = self.create(User)
        entry = self.create_entry(project=project)
        get_user_mocked_func.return_value = user2

        old_assignment_count = Assignment.objects.count()
        lead = self.create(Lead, project=project)
        lead.assignee.add(user1)
        entry_comment = self.create(EntryComment, entry=entry)
        entry_comment.assignees.add(user1)

        new_assignment_count = Assignment.objects.count()
        self.assertEqual(new_assignment_count, old_assignment_count + 2)

        # try deleting lead and entry_comment
        lead.delete()
        entry_comment.delete()
        new_assignment_count = Assignment.objects.count()
        self.assertEqual(new_assignment_count, old_assignment_count)  # no lead and entry_comment should be there
