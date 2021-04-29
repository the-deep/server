from deep.tests import TestCase
from entry.models import Entry
from notification.models import Notification
from project.models import ProjectMembership
from quality_assurance.models import (
    # EntryReviewComment,
    CommentType,
    EntryReviewComment,
)

VerifiedByQs = Entry.verified_by.through.objects


class QualityAccuranceTests(TestCase):
    def test_entry_review_comment_basic_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)

        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        project.add_member(user1, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user2, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user3, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])

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

    def test_entry_review_comment_verify_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        project.add_member(user1, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user2, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user3, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])

        self.authenticate(user1)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.COMMENT,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        assert VerifiedByQs.filter(entry=entry).count() == 0

        # Should include is_verified_by_current_user as False
        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert not response.data['results'][0]['is_verified_by_current_user']

        # Verify
        data = {
            'text': 'This is a test comment for approvable',
            'comment_type': CommentType.VERIFY,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        assert VerifiedByQs.filter(entry=entry).count() == 1

        # Should include is_verified_by_current_user as True
        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert response.data['results'][0]['is_verified_by_current_user']

        self.authenticate(user2)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.VERIFY,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        assert VerifiedByQs.filter(entry=entry).count() == 2

        # Unverify
        data = {
            'text': 'This is a test comment for unapprovable',
            'comment_type': CommentType.UNVERIFY,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        assert VerifiedByQs.filter(entry=entry).count() == 1

        # Can't verify already verify
        self.authenticate(user1)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.VERIFY,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)

        assert VerifiedByQs.filter(entry=entry).count() == 1

        # Can't unverify not verify
        self.authenticate(user2)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.UNVERIFY,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)
        self.authenticate(user3)
        data = {
            'text': 'This is a test comment',
            'comment_type': CommentType.UNVERIFY,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)

        assert VerifiedByQs.filter(entry=entry).count() == 1

    def test_entry_review_comment_project_qa_badge_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user1_membership = project.add_member(user1, role=self.normal_role)

        self.authenticate(user1)
        for comment_type in [CommentType.CONTROL, CommentType.UNCONTROL]:
            user1_membership.badges = []
            user1_membership.save()

            data = {
                'text': 'This is a test comment',
                'comment_type': comment_type,
            }
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_400(response)

            user1_membership.badges = [ProjectMembership.BadgeType.QA]
            user1_membership.save()

            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_201(response)

    def test_entry_review_comment_control_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        project.add_member(user1, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user2, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user3, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])

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
        assert entry.controlled
        assert entry.controlled_changed_by == user1

        # Control using same user again
        data = {
            'text': 'This is a test comment to again control already verified',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)
        entry.refresh_from_db()
        assert entry.controlled
        assert entry.controlled_changed_by == user1

        # Control using another user again
        self.authenticate(user2)
        data = {
            'text': 'This is a test comment to again control already verified',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_400(response)
        entry.refresh_from_db()
        assert entry.controlled
        assert entry.controlled_changed_by == user1

        # Uncontrol (any users can also uncontrol)
        self.authenticate(user2)
        data = {
            'text': 'This is a test comment for uncontrol',
            'comment_type': CommentType.UNCONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)
        entry.refresh_from_db()
        assert not entry.controlled
        assert entry.controlled_changed_by == user2

        for user in [user1, user2]:
            self.authenticate(user)
            # Can't uncontrol already uncontrol
            data = {
                'text': 'This is a test comment',
                'comment_type': CommentType.UNVERIFY,
            }
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_400(response)
            entry.refresh_from_db()
            assert not entry.controlled
            assert entry.controlled_changed_by == user2

    def test_entry_review_comment_summary_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        project.add_member(user1, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user2, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user3, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user4, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])

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
                'text': 'This is a verify comment',
                'comment_type': CommentType.VERIFY,
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
        assert len(response.data['summary']['verified_by']) == 2
        assert response.data['summary']['controlled']
        assert response.data['summary']['controlled_changed_by']['id'] == user4.pk

    def test_entry_filter_verified_count_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)

        for user in range(0, 3):
            user = self.create_user()
            project.add_member(user, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
            self.authenticate(user)
            data = {
                'text': 'This is a verify comment',
                'comment_type': CommentType.VERIFY,
            }
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            self.assert_201(response)

        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert response.data['results'][0]['verified_by_count'] == 3
        assert not response.data['results'][0]['controlled']

        self.authenticate(user)
        data = {
            'text': 'This is a control comment',
            'comment_type': CommentType.CONTROL,
        }
        response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
        self.assert_201(response)

        response = self.client.post('/api/v1/entries/filter/', data={'project': project.pk})
        self.assert_200(response)
        assert response.data['results'][0]['verified_by_count'] == 3
        assert response.data['results'][0]['controlled']

    def test_entry_review_comment_text_required_api(self):
        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        project.add_member(user1, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])

        for comment_type, text_required in [
                (None, True),  # Default is CommentType.COMMENT
                (CommentType.COMMENT, True),
                (CommentType.VERIFY, False),
                (CommentType.UNVERIFY, True),
                (CommentType.CONTROL, False),
                (CommentType.UNCONTROL, True),
        ]:
            self.authenticate(user1)
            data = {}
            if comment_type:
                data['comment_type'] = comment_type
            response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
            if text_required:
                self.assert_400(response)
                data['text'] = 'This is a comment'
                response = self.client.post(f'/api/v1/entries/{entry.pk}/review-comments/', data=data)
                self.assert_201(response)
            else:
                self.assert_201(response)

    def test_entry_review_comment_notification(self):
        def _get_comment_users_pk(pk):
            return set(
                EntryReviewComment.objects.get(pk=pk).get_related_users().values_list('pk', flat=True)
            )

        def _clean_comments(project):
            return EntryReviewComment.objects.filter(entry__project=project).delete()

        def _clear_notifications():
            return Notification.objects.all().delete()

        def _get_notifications_receivers():
            return set(
                Notification.objects.values_list('receiver', flat=True)
            ), set(
                Notification.objects.values_list('notification_type', flat=True).distinct()
            )

        project = self.create_project()
        entry = self.create_entry(project=project)
        user1 = self.create_user()
        user2 = self.create_user()
        user3 = self.create_user()
        user4 = self.create_user()
        project.add_member(user1, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user2, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user3, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        project.add_member(user4, role=self.normal_role, badges=[ProjectMembership.BadgeType.QA])
        url = f'/api/v1/entries/{entry.pk}/review-comments/'

        self.authenticate(user1)

        # Create a commit
        _clear_notifications()
        data = {
            'text': 'This is a comment',
            'comment_type': CommentType.COMMENT,
            'mentioned_users': [user2.pk],
        }
        # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            comment_id = self.client.post(url, data=data).json()['id']
        assert _get_comment_users_pk(comment_id) == set([user2.pk])
        assert _get_notifications_receivers() == (
            set([user2.pk]),
            set([Notification.ENTRY_REVIEW_COMMENT_ADD]),
        )

        # Create a commit (multiple mentioned_users)
        _clear_notifications()
        data = {
            'text': 'This is a comment',
            'comment_type': CommentType.COMMENT,
            'mentioned_users': [user2.pk, user3.pk, user1.pk],
        }
        # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            comment_id = self.client.post(url, data=data).json()['id']
        assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
        assert _get_notifications_receivers() == (
            set([user2.pk, user3.pk]),
            set([Notification.ENTRY_REVIEW_COMMENT_ADD]),
        )

        # Create a commit different comment_type
        for comment_type in [
            CommentType.VERIFY, CommentType.UNVERIFY,
            CommentType.CONTROL, CommentType.UNCONTROL,
        ]:
            _clean_comments(project)
            _clear_notifications()
            data = {
                'text': 'This is a comment',
                'comment_type': comment_type,
                'mentioned_users': [user1.pk, user2.pk, user3.pk],
            }
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                comment_id = self.client.post(url, data=data).json()['id']
            assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
            assert _get_notifications_receivers() == (
                set([user2.pk, user3.pk]),
                set([Notification.ENTRY_REVIEW_COMMENT_ADD]),
            )

            _clear_notifications()
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.patch(f'{url}{comment_id}/', data=data)
                self.assert_200(resp)
            assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
            assert _get_notifications_receivers() == (set(), set())  # No new notifications are created

            _clear_notifications()
            data['text'] = 'this is a new comment text'
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.patch(f'{url}{comment_id}/', data=data)
                self.assert_200(resp)
            assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
            assert _get_notifications_receivers() == (
                set([user2.pk, user3.pk]),
                set([Notification.ENTRY_REVIEW_COMMENT_MODIFY]),
            )  # New notifications are created

            _clear_notifications()
            data['mentioned_users'].append(user4.pk)
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                resp = self.client.patch(f'{url}{comment_id}/', data=data)
                self.assert_200(resp)
            assert _get_comment_users_pk(comment_id) == set([user4.pk, user2.pk, user3.pk])
            assert _get_notifications_receivers() == (
                set([user4.pk]),
                set([Notification.ENTRY_REVIEW_COMMENT_MODIFY]),
            )  # New notifications are created only for user2
