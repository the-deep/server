from deep.tests import TestCase
from quality_assurance.models import (
    # EntryReviewComment,
    CommentType,
)


class QualityAccuranceTests(TestCase):
    def test_entry_review_comment_basic_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)

        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        project.add_member(user1, role=self.normal_role)
        project.add_member(user2, role=self.normal_role)
        project.add_member(user3, role=self.normal_role)

        self.authenticate(user1)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.COMMENT,
            'mentioned_users': [user1.pk, user2.pk, user3.pk],
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        review_comment1_pk = response.data['id']

        response = self.client.get(f'/api/v1/entries/{entry.pk}/review-comments/')
        self.assert_200(response)
        assert len(response.data['results']) == 1

        # Update only allowd by comment creater
        data['text'] = 'This is updated text comment'
        response = self.client.put(f'/api/v1/entries/{entry.pk}/review-comments/{review_comment1_pk}/', data=data)
        self.assert_200(response)
        self.assertEqual(response.data['text_history'][0]['text'], data['text'])
        self.authenticate(user2)
        response = self.client.put(f'/api/v1/entries/{entry.pk}/review-comments/{review_comment1_pk}/', data=data)
        self.assert_403(response)

        self.authenticate(user2)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.COMMENT,
            'mentioned_users': [user1.pk, user2.pk, user3.pk],
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        review_comment1_pk = response.data['id']

        response = self.client.get(f'/api/v1/entries/{entry.pk}/review-comments/')
        self.assert_200(response)
        assert len(response.data['results']) == 2

        self.authenticate(user4)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.COMMENT,
            'mentioned_users': [user1.pk, user2.pk, user3.pk],
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_403(response)
        response = self.client.get(f'/api/v1/entries/{entry.pk}/review-comments/')
        self.assert_403(response)
