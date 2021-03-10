from deep.tests import TestCase
from entry.models import Entry
from quality_assurance.models import (
    # EntryReviewComment,
    CommentType,
)

ApprovedByQs = Entry.approved_by.through.objects


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

    def test_entry_review_comment_approve_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        project.add_member(user1, role=self.normal_role)
        project.add_member(user2, role=self.normal_role)
        project.add_member(user3, role=self.normal_role)

        self.authenticate(user1)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.COMMENT,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        assert ApprovedByQs.filter(entry=entry).count() == 0

        # Should include is_approved_by_current_user as False
        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert not response.data['results'][0]['is_approved_by_current_user']

        # Approve
        data = {
            'text': 'This is a test comment for approvable',
            'comment_type': CommentType.APPROVE,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        assert ApprovedByQs.filter(entry=entry).count() == 1

        # Should include is_approved_by_current_user as True
        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert response.data['results'][0]['is_approved_by_current_user']

        self.authenticate(user2)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.APPROVE,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        assert ApprovedByQs.filter(entry=entry).count() == 2

        # Unapprove
        data = {
            'text': 'This is a test comment for unapprovable',
            'comment_type': CommentType.UNAPPROVE,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        assert ApprovedByQs.filter(entry=entry).count() == 1

        # Can't approve already approve
        self.authenticate(user1)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.APPROVE,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)

        assert ApprovedByQs.filter(entry=entry).count() == 1

        # Can't unapprove not approve
        self.authenticate(user2)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.UNAPPROVE,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)
        self.authenticate(user3)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.UNAPPROVE,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)

        assert ApprovedByQs.filter(entry=entry).count() == 1

    def test_entry_review_comment_control_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        project.add_member(user1, role=self.normal_role)
        project.add_member(user2, role=self.normal_role)
        project.add_member(user3, role=self.normal_role)

        self.authenticate(user1)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.COMMENT,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        # Control
        data = {
            'text': 'This is a test comment for control/verify',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        entry.refresh_from_db()
        assert entry.verified
        assert entry.verification_last_changed_by == user1

        # Control using same user again
        data = {
            'text': 'This is a test comment to again control/verify already verified',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)
        entry.refresh_from_db()
        assert entry.verified
        assert entry.verification_last_changed_by == user1

        # Control using another user again
        self.authenticate(user2)
        data = {
            'text': 'This is a test comment to again control/verify already verified',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)
        entry.refresh_from_db()
        assert entry.verified
        assert entry.verification_last_changed_by == user1

        # Uncontrol (any users can also uncontrol)
        self.authenticate(user2)
        data = {
            'text': 'This is a test comment for uncontrol',
            'comment_type': CommentType.UNCONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        entry.refresh_from_db()
        assert not entry.verified
        assert entry.verification_last_changed_by == user2

        for user in [user1, user2]:
            self.authenticate(user)
            # Can't uncontrol already uncontrol
            data = {
                'text': 'This is a test comment',
                'comment_type': CommentType.UNAPPROVE,
            }
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_400(response)
            entry.refresh_from_db()
            assert not entry.verified
            assert entry.verification_last_changed_by == user2

    def test_entry_review_comment_summary_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        project.add_member(user1, role=self.normal_role)
        project.add_member(user2, role=self.normal_role)
        project.add_member(user3, role=self.normal_role)
        project.add_member(user4, role=self.normal_role)

        self.authenticate(user1)
        data = {
            'text': 'This is a comment',
            'comment_type': CommentType.COMMENT,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        for user in [user2, user3]:
            self.authenticate(user)
            data = {
                'text': 'This is a approve comment',
                'comment_type': CommentType.APPROVE,
            }
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_201(response)

        self.authenticate(user4)
        data = {
            'text': 'This is a control comment',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        response = self.client.get(f'/api/v1/entries/{entry.pk}/review-comments/')
        assert 'summary' in response.data
        assert len(response.data['summary']['approved_by']) == 2
        assert response.data['summary']['verified']
        assert response.data['summary']['verification_last_changed_by']['id'] == user4.pk

    def test_entry_filter_approved_count_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)

        for user in range(0, 3):
            user = self.create_user()
            project.add_member(user, role=self.normal_role)
            self.authenticate(user)
            data = {
                'text': 'This is a approve comment',
                'comment_type': CommentType.APPROVE,
            }
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_201(response)

        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert response.data['results'][0]['approved_by_count'] == 3
        assert not response.data['results'][0]['verified']

        self.authenticate(user)
        data = {
            'text': 'This is a control comment',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert response.data['results'][0]['approved_by_count'] == 3
        assert response.data['results'][0]['verified']

    # TODO: notification
