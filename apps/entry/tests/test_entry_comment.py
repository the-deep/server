from deep.tests import TestCase
from entry.models import EntryComment
from notification.models import Notification


class EntryCommentTests(TestCase):
    def setUp(self):
        super().setUp()
        self.entry = self.create_entry()
        self.comment = self.create(EntryComment, **{
            'entry': self.entry,
            'assignees': [self.user],
            'text': 'This is a comment text',
            'parent': None,
        })
        assert self.comment.is_resolved is False
        self.entry.project.add_member(self.root_user)

    def test_create_comment(self):
        url = f'/api/v1/entries/{self.entry.pk}/entry-comments/'
        data = {
            'assignees': [self.user.pk],
            'text': 'This is first comment',
            'parent': None,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        # Throw error if assignee is not provided for root comment
        data.pop('assignees')
        response = self.client.post(url, data)
        self.assert_400(response)
        data['assignees'] = [self.user.pk]

        # Throw error if text is not provided
        data['text'] = None
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_create_comment_reply(self):
        entry_2 = self.create_entry()

        url = f'/api/v1/entries/{entry_2.pk}/entry-comments/'
        data = {
            'assignees': [self.user.pk],
            'text': 'This is first comment',
            'parent': self.comment.pk,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'parent' in response.data['errors']

        comment_2 = self.create(EntryComment, **{
            'entry': entry_2,
            'assignees': [self.user],
            'text': 'This is a comment text',
            'parent': None,
        })
        data['parent'] = comment_2.pk
        response = self.client.post(url, data)
        self.assert_201(response)
        assert response.data['entry'] == entry_2.pk, 'Should be same to parent entry'
        assert response.data['assignees'] == [], 'There should be no assignee in reply comment'

    def test_comment_text_history(self):
        url = f'/api/v1/entries/{self.entry.pk}/entry-comments/'
        data = {
            'assignees': [self.user.pk],
            'text': 'This is first comment',
            'parent': None,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        comment_id = response.json()['id']

        # Patch new text
        new_text = 'this is second comment'
        response = self.client.patch(f'{url}{comment_id}/', {'text': new_text})
        r_data = response.json()
        assert r_data['text'] == new_text
        assert len(r_data['textHistory']) == 2

        # Patch same text again
        response = self.client.patch(f'{url}{comment_id}/', {'text': new_text})
        r_data = response.json()
        assert r_data['text'] == new_text
        assert len(r_data['textHistory']) == 2

    def test_comment_resolve(self):
        url = f'/api/v1/entries/{self.entry.pk}/entry-comments/'
        data = {
            'assignees': [self.user.pk],
            'text': 'This is first comment',
            'parent': None,
        }

        self.authenticate(self.root_user)
        # Add comment
        response = self.client.post(url, data)
        r_data = response.json()
        self.assert_201(response)
        assert r_data['isResolved'] is False
        parent_comment_id_1 = r_data['id']

        self.authenticate(self.user)
        # Add comment
        response = self.client.post(url, data)
        r_data = response.json()
        self.assert_201(response)
        assert r_data['isResolved'] is False
        parent_comment_id = r_data['id']

        # Add reply comment
        data['parent'] = parent_comment_id
        response = self.client.post(url, data)
        r_data = response.json()
        self.assert_201(response)
        assert r_data['isResolved'] is False
        comment_id = r_data['id']

        # Throw error if resolved request is send for reply
        response = self.client.post(f'{url}{comment_id}/resolve/')
        self.assert_400(response)

        # Send resolve request to comment
        response = self.client.post(f'{url}{parent_comment_id}/resolve/')
        r_data = response.json()
        assert r_data['isResolved'] is True

        # Throw error if reply is added for resolved comment
        data['parent'] = parent_comment_id
        response = self.client.post(url, data)
        self.assert_400(response)

        # Throw error if request send to resolved other user's comment
        response = self.client.post(f'{url}{parent_comment_id_1}/resolve/')
        r_data = response.json()
        self.assert_403(response)

    def test_comment_delete(self):
        url = f'/api/v1/entries/{self.entry.pk}/entry-comments/'
        user1 = self.user
        user2 = self.root_user
        data = {
            'assignees': [self.user.pk],
            'text': 'This is first comment',
            'parent': None,
        }

        self.authenticate(user1)
        # Add comment by user1
        response = self.client.post(url, data)
        self.assert_201(response)
        comment1_id = response.json()['id']

        self.authenticate(user2)
        # Add comment by user2
        response = self.client.post(url, data)
        self.assert_201(response)
        comment2_id = response.json()['id']

        self.authenticate(user1)
        response = self.client.delete(f'{url}{comment1_id}/')
        self.assert_204(response)
        response = self.client.delete(f'{url}{comment2_id}/')
        self.assert_403(response)

    def test_comment_notification(self):
        """
        Used to send Notification using DEEP and Email
        """
        def _get_comment_users_pk(pk):
            return set(
                EntryComment.objects.get(pk=pk).get_related_users().values_list('pk', flat=True)
            )

        def _clear_notifications():
            return Notification.objects.all().delete()

        def _get_notifications_receivers():
            return set(
                Notification.objects.values_list('receiver', flat=True)
            ), set(
                Notification.objects.values_list('notification_type', flat=True).distinct()
            )

        reviewer = self.create_user()
        tagger1 = self.create_user()
        tagger2 = self.create_user()
        for user in [reviewer, tagger1, tagger2]:
            self.entry.project.add_member(user, role=self.normal_role)

        url = f'/api/v1/entries/{self.entry.pk}/entry-comments/'
        data = {
            'assignees': [tagger1.pk],
            'text': 'This is first comment',
            'parent': None,
        }

        # Create a commit
        _clear_notifications()
        self.authenticate(reviewer)
        # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            comment1_id = self.client.post(url, data).json()['id']
        assert _get_comment_users_pk(comment1_id) == set([tagger1.pk])
        assert _get_notifications_receivers() == (
            set([tagger1.pk]),
            set([Notification.ENTRY_COMMENT_ADD]),
        )

        data['parent'] = comment1_id
        data['assignees'] = []

        # Create a reply 1
        _clear_notifications()
        self.authenticate(tagger1)
        data['text'] = 'this is first reply'
        with self.captureOnCommitCallbacks(execute=True):
            reply1_id = self.client.post(url, data).json()['id']
        assert _get_comment_users_pk(reply1_id) == set([reviewer.pk])
        assert _get_notifications_receivers() == (
            set([reviewer.pk]),
            set([Notification.ENTRY_COMMENT_REPLY_ADD]),
        )

        # Create a reply 2
        _clear_notifications()
        self.authenticate(reviewer)
        data['text'] = 'this is second reply'
        with self.captureOnCommitCallbacks(execute=True):
            reply2_id = self.client.post(url, data).json()['id']
        assert _get_comment_users_pk(reply2_id) == set([tagger1.pk])
        assert _get_notifications_receivers() == (
            set([tagger1.pk]),  # Targeted users for notification
            set([Notification.ENTRY_COMMENT_REPLY_ADD]),  # Notification type
        )

        # Create a reply 3
        _clear_notifications()
        self.authenticate(tagger2)
        data['text'] = 'this is third reply'
        with self.captureOnCommitCallbacks(execute=True):
            reply3_id = self.client.post(url, data).json()['id']
        assert _get_comment_users_pk(reply3_id) == set([reviewer.pk, tagger1.pk])
        assert _get_notifications_receivers() == (
            set([reviewer.pk, tagger1.pk]),
            set([Notification.ENTRY_COMMENT_REPLY_ADD]),
        )

        # Update reply 3
        _clear_notifications()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.patch(f'{url}{reply3_id}/', {
                'text': 'updating the third reply text',
            })
        assert _get_comment_users_pk(reply3_id) == set([reviewer.pk, tagger1.pk])
        assert _get_notifications_receivers() == (
            set([reviewer.pk, tagger1.pk]),
            set([Notification.ENTRY_COMMENT_REPLY_MODIFY]),
        )

        # Change assigne for the commit
        _clear_notifications()
        self.authenticate(reviewer)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.patch(f'{url}{comment1_id}/', {
                'assignees': [tagger2.pk],
            })
        assert _get_notifications_receivers() == (
            set([tagger1.pk, tagger2.pk]),
            set([Notification.ENTRY_COMMENT_ASSIGNEE_CHANGE]),
        )

        # Update comment text
        _clear_notifications()
        self.authenticate(reviewer)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.patch(f'{url}{comment1_id}/', {
                'text': 'updating the comment text',
            })
        assert _get_notifications_receivers() == (
            set([tagger1.pk, tagger2.pk]),
            set([Notification.ENTRY_COMMENT_MODIFY]),
        )

        # Resolve comment
        _clear_notifications()
        self.authenticate(reviewer)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(f'{url}{comment1_id}/resolve/')
        assert _get_notifications_receivers() == (
            set([tagger1.pk, tagger2.pk]),
            set([Notification.ENTRY_COMMENT_RESOLVED]),
        )

    def test_entry_comment_put(self):
        user = self.create_user()
        user1 = self.create_user()
        user2 = self.create_user()

        project = self.create_project()
        lead = self.create_lead(created_by=user, project=project)
        entry = self.create_entry(created_by=user, project=project, lead=lead)
        [project.add_member(u) for u in [user, user1, user2]]

        # Non member user
        data = {
            'text': 'Test comment',
            'assignees': [user1.pk, user2.pk],
        }

        self.authenticate(user)

        url = f'/api/v1/entries/{entry.pk}/entry-comments/'
        response = self.client.post(url, data)
        self.assert_201(response)
        comment_id = response.json()['id']

        url = f'/api/v1/entries/{entry.pk}/entry-comments/{comment_id}/'
        data['text'] = 'updated test comment'
        data['assignees'] = [user1.pk]
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_entry_comment_permissions(self):
        """
        Test
        - if users w/o can create entry comment
        - if users w/o can assigne member/non-member to the entry comment
        """
        user1 = self.create_user()  # Comment creater
        user2 = self.create_user()  # Project member
        user3 = self.create_user()  # Non-project member

        project = self.create_project(role=self.admin_role)
        lead = self.create_lead(project=project)
        entry = self.create_entry(lead=lead, project=project)
        entry.project.add_member(user2)

        url = f'/api/v1/entries/{entry.id}/entry-comments/'
        data = {
            'text': 'test_entry_comment',
            'assignees': [user2.id],
        }
        self.authenticate(user1)

        # Check if non-member can create entry comment
        response = self.client.post(url, data)
        self.assert_403(response)

        # Check if member can create entry comment
        entry.project.add_member(user1)
        response = self.client.post(url, data)
        resp_data = response.data
        self.assert_201(response)

        # Check if member can create entry comment with non-member assignee
        data['assignees'] = [user3.id]
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'assignees' in response.data['errors']

        data['assignees'] = [user2.id]
        # Comment owner should be able to update comment
        response = self.client.put(f"{url}{resp_data['id']}/", data)
        self.assert_200(response)

        # Comment non-owner shouldn't be able to update comment
        self.authenticate(user2)
        response = self.client.put(f"{url}{resp_data['id']}/", data)
        self.assert_403(response)
