from deep.tests import TestCase
from entry.models import EntryComment


class EntryCommentTests(TestCase):
    def setUp(self):
        super().setUp()
        self.entry = self.create_entry()
        self.comment = self.create(EntryComment, **{
            'entry': self.entry,
            'assignee': self.user,
            'text': 'This is a comment text',
            'parent': None,
        })
        assert self.comment.is_resolved is False

    def test_create_comment(self):
        url = '/api/v1/entry-comments/'
        data = {
            'entry': self.entry.pk,
            'assignee': self.user.pk,
            'text': 'This is first comment',
            'parent': None,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        # Throw error if assignee is not provided for root comment
        data.pop('assignee')
        response = self.client.post(url, data)
        self.assert_400(response)
        data['assignee'] = self.user.pk

        # Throw error if text is not provided
        data['text'] = None
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_create_comment_reply(self):
        entry_2 = self.create_entry()

        url = '/api/v1/entry-comments/'
        data = {
            'entry': entry_2.pk,
            'assignee': self.user.pk,
            'text': 'This is first comment',
            'parent': self.comment.pk,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        r_data = response.json()
        assert r_data['entry'] == self.entry.pk, 'Should be same to parent entry'
        assert r_data['assignee'] is None, 'There should be no assignee in reply comment'

    def test_comment_text_history(self):
        url = '/api/v1/entry-comments/'
        data = {
            'entry': self.entry.pk,
            'assignee': self.user.pk,
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
        url = '/api/v1/entry-comments/'
        data = {
            'entry': self.entry.pk,
            'assignee': self.user.pk,
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
        response = self.client.post(f'{url}{comment_id}/resolved/')
        self.assert_400(response)

        # Send resolved request to comment
        response = self.client.post(f'{url}{parent_comment_id}/resolved/')
        r_data = response.json()
        assert r_data['isResolved'] is True

        # Throw error if reply is added for resolved comment
        data['parent'] = parent_comment_id
        response = self.client.post(url, data)
        self.assert_400(response)

        # Throw error if request send to resolved other user's comment
        response = self.client.post(f'{url}{parent_comment_id_1}/resolved/')
        r_data = response.json()
        self.assert_400(response)

    def test_comment_delete(self):
        url = '/api/v1/entry-comments/'
        user1 = self.user
        user2 = self.root_user
        data = {
            'entry': self.entry.pk,
            'assignee': self.user.pk,
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
