from utils.graphene.tests import GraphQLTestCase

from quality_assurance.models import EntryReviewComment
from project.models import ProjectMembership
from notification.models import Notification
from entry.models import Entry

from user.factories import UserFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory

from quality_assurance.factories import EntryReviewCommentFactory


VerifiedByQs = Entry.verified_by.through.objects


class TestQualityAssuranceMutation(GraphQLTestCase):

    CREATE_ENTRY_REVIEW_COMMENT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: EntryReviewCommentInputType!) {
          project(id: $projectId) {
            entryReviewCommentCreate(data: $input) {
              ok
              errors
              result {
                id
                commentType
                createdAt
                text
                createdBy {
                  id
                  profile {
                      displayName
                  }
                }
                mentionedUsers {
                  id
                  profile {
                      displayName
                  }
                }
                textHistory {
                  id
                  createdAt
                  text
                }
              }
            }
          }
        }
    '''

    UPDATE_ENTRY_REVIEW_COMMENT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $reviewCommentId: ID!, $input: EntryReviewCommentInputType!) {
          project(id: $projectId) {
            entryReviewCommentUpdate(id: $reviewCommentId data: $input) {
              ok
              errors
              result {
                id
                commentType
                createdAt
                text
                createdBy {
                  id
                  profile {
                      displayName
                  }
                }
                mentionedUsers {
                  id
                  profile {
                      displayName
                  }
                }
                textHistory {
                  id
                  createdAt
                  text
                }
              }
            }
          }
        }
    '''

    DELETE_ENTRY_REVIEW_COMMENT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $commentId: ID!) {
          project(id: $projectId) {
            entryReviewCommentDelete(id: $commentId) {
              ok
              errors
              result {
                id
                commentType
                createdAt
                text
                createdBy {
                  id
                  profile {
                      displayName
                  }
                }
                mentionedUsers {
                  id
                  profile {
                      displayName
                  }
                }
                textHistory {
                  id
                  createdAt
                  text
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.qa_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.non_member_user = UserFactory.create()
        self.af = AnalysisFrameworkFactory.create()
        self.project = ProjectFactory.create(analysis_framework=self.af)
        self.lead = LeadFactory.create(project=self.project)
        self.entry = EntryFactory.create(lead=self.lead)
        # Add member to project
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader_non_confidential)
        self.project.add_member(self.member_user, role=self.project_role_member)
        self.project.add_member(self.qa_member_user, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])

    def _query_check(self, mutation_input, review_comment_id=None, **kwargs):
        variables = {'projectId': self.project.id}
        query = self.CREATE_ENTRY_REVIEW_COMMENT_QUERY
        if review_comment_id:
            query = self.UPDATE_ENTRY_REVIEW_COMMENT_QUERY
            variables['reviewCommentId'] = review_comment_id
        return self.query_check(
            query,
            minput=mutation_input,
            mnested=['project'],
            variables=variables,
            **kwargs
        )

    def test_entry_review_comment_create(self):
        minput = {
            'entry': self.entry.id,
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
            # 'mentionedUsers': [self.readonly_member_user.pk, self.qa_member_user.pk],
        }

        def _get_notifications_receivers():
            return set(
                Notification.objects.values_list('receiver', flat=True)
            ), set(
                Notification.objects.values_list('notification_type', flat=True).distinct()
            )

        # -- Without login
        self._query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        self._query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        self._query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)

        # Invalid input (Comment without text)
        self.entry.controlled = True
        self.entry.save(update_fields=('controlled',))
        minput = {
            'entry': self.entry.id,
            'commentType': self.genum(EntryReviewComment.CommentType.CONTROL),
        }

        self._query_check(minput, okay=False)

        # Control
        self.entry.controlled = False
        self.entry.save(update_fields=('controlled',))
        self._query_check(minput, okay=False)
        self.force_login(self.qa_member_user)
        minput['commentType'] = self.genum(EntryReviewComment.CommentType.UNCONTROL)
        self._query_check(minput, okay=False)
        minput['commentType'] = self.genum(EntryReviewComment.CommentType.CONTROL)
        self._query_check(minput, okay=True)  # If request by a QA User

        minput['commentType'] = self.genum(EntryReviewComment.CommentType.UNCONTROL)
        self.force_login(self.member_user)
        self._query_check(minput, okay=False)
        self.force_login(self.qa_member_user)
        self._query_check(minput, okay=False)  # Text is required
        minput['text'] = 'sample text'
        self._query_check(minput, okay=True)  # If request by a QA User

        # Verify
        self.force_login(self.member_user)
        minput.pop('text')
        minput['commentType'] = self.genum(EntryReviewComment.CommentType.VERIFY)
        self._query_check(minput, okay=True)
        minput['commentType'] = self.genum(EntryReviewComment.CommentType.VERIFY)
        self._query_check(minput, okay=False)
        minput['commentType'] = self.genum(EntryReviewComment.CommentType.UNVERIFY)
        self._query_check(minput, okay=False)
        minput['text'] = 'sample text'
        self._query_check(minput, okay=True)
        minput['commentType'] = self.genum(EntryReviewComment.CommentType.UNVERIFY)
        self._query_check(minput, okay=False)

    def test_entry_review_comment_basic_api(self):
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()
        user4 = UserFactory.create()
        self.project.add_member(user1, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user2, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user3, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])

        self.force_login(user1)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
            'mentionedUsers': [user1.pk, user2.pk, user3.pk],
        }
        comment_pk = self._query_check(data, okay=True)['data']['project']['entryReviewCommentCreate']['result']['id']

        assert self.entry.review_comments.count() == 1

        # Update only allowd by comment creater
        data['text'] = 'This is updated text comment'
        content = self._query_check(
            data, review_comment_id=comment_pk, okay=True)['data']['project']['entryReviewCommentUpdate']
        self.assertEqual(content['result']['textHistory'][0]['text'], data['text'])
        self.assertEqual(content['result']['text'], data['text'])
        self.force_login(user2)
        self._query_check(data, review_comment_id=comment_pk, okay=False)

        self.force_login(user2)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
            'mentionedUsers': [user1.pk, user2.pk, user3.pk],
        }
        self._query_check(data, okay=True)

        assert self.entry.review_comments.count() == 2

        self.force_login(user4)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
            'mentionedUsers': [user1.pk, user2.pk, user3.pk],
        }
        self._query_check(data, assert_for_error=True)

    def test_entry_review_comment_verify_api(self):
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()
        self.project.add_member(user1, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user2, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user3, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])

        self.force_login(user1)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
        }
        self._query_check(data, okay=True)
        assert VerifiedByQs.filter(entry=self.entry).count() == 0

        # Verify
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment for approvable',
            'commentType': self.genum(EntryReviewComment.CommentType.VERIFY),
        }
        self._query_check(data, okay=True)
        assert VerifiedByQs.filter(entry=self.entry).count() == 1

        self.force_login(user2)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.VERIFY),
        }
        self._query_check(data, okay=True)
        assert VerifiedByQs.filter(entry=self.entry).count() == 2

        # Unverify
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment for unapprovable',
            'commentType': self.genum(EntryReviewComment.CommentType.UNVERIFY),
        }
        self._query_check(data, okay=True)

        assert VerifiedByQs.filter(entry=self.entry).count() == 1

        # Can't verify already verify
        self.force_login(user1)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.VERIFY),
        }
        self._query_check(data, okay=False)

        assert VerifiedByQs.filter(entry=self.entry).count() == 1

        # Can't unverify not verify
        self.force_login(user2)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.UNVERIFY),
        }
        self._query_check(data, okay=False)

        self.force_login(user3)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.UNVERIFY),
        }
        self._query_check(data, okay=False)

        assert VerifiedByQs.filter(entry=self.entry).count() == 1

    def test_entry_review_comment_project_qa_badge_api(self):
        user1 = UserFactory.create()
        user1_membership = self.project.add_member(user1, role=self.project_role_member)

        self.force_login(user1)
        for comment_type in [
            EntryReviewComment.CommentType.CONTROL,
            EntryReviewComment.CommentType.UNCONTROL,
        ]:
            user1_membership.badges = []
            user1_membership.save()

            data = {
                'entry': self.entry.pk,
                'text': 'This is a test comment',
                'commentType': self.genum(comment_type),
            }
            self._query_check(data, okay=False)

            user1_membership.badges = [ProjectMembership.BadgeType.QA]
            user1_membership.save()

            self._query_check(data, okay=True)

    def test_entry_review_comment_control_api(self):
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()
        self.project.add_member(user1, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user2, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user3, role=self.project_role_member)

        self.force_login(user1)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
        }
        self._query_check(data, okay=True)

        # Control
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment for control/verify',
            'commentType': self.genum(EntryReviewComment.CommentType.CONTROL),
        }
        self._query_check(data, okay=True)
        self.entry.refresh_from_db()
        assert self.entry.controlled
        assert self.entry.controlled_changed_by == user1

        # Control using same user again
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment to again control already verified',
            'commentType': self.genum(EntryReviewComment.CommentType.CONTROL),
        }
        self._query_check(data, okay=False)
        self.entry.refresh_from_db()
        assert self.entry.controlled
        assert self.entry.controlled_changed_by == user1

        # Control using another user again
        self.force_login(user2)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment to again control already verified',
            'commentType': self.genum(EntryReviewComment.CommentType.CONTROL),
        }
        self._query_check(data, okay=False)
        self.entry.refresh_from_db()
        assert self.entry.controlled
        assert self.entry.controlled_changed_by == user1

        # Uncontrol (any users can also uncontrol)
        self.force_login(user2)
        data = {
            'entry': self.entry.pk,
            'text': 'This is a test comment for uncontrol',
            'commentType': self.genum(EntryReviewComment.CommentType.UNCONTROL),
        }
        self._query_check(data, okay=True)
        self.entry.refresh_from_db()
        assert not self.entry.controlled
        assert self.entry.controlled_changed_by == user2

        for user in [user1, user2]:
            self.force_login(user)
            # Can't uncontrol already uncontrol
            data = {
                'entry': self.entry.pk,
                'text': 'This is a test comment',
                'commentType': self.genum(EntryReviewComment.CommentType.UNVERIFY),
            }
            self._query_check(data, okay=False)
            self.entry.refresh_from_db()
            assert not self.entry.controlled
            assert self.entry.controlled_changed_by == user2

    def test_entry_review_comment_create_text_required(self):
        self.force_login(self.qa_member_user)

        # Text required
        for comment_type, text_required in [
                (None, True),  # Default is CommentType.COMMENT
                (EntryReviewComment.CommentType.COMMENT, True),
                (EntryReviewComment.CommentType.VERIFY, False),
                (EntryReviewComment.CommentType.UNVERIFY, True),
                (EntryReviewComment.CommentType.CONTROL, False),
                (EntryReviewComment.CommentType.UNCONTROL, True),
        ]:
            _minput = {'entry': self.entry.pk}
            if comment_type:
                _minput['commentType'] = self.genum(comment_type)
            if text_required:
                self._query_check(_minput, okay=False)
                _minput['text'] = 'This is a comment'
                self._query_check(_minput, okay=True)
            else:
                self._query_check(_minput, okay=True)

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

        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()
        user4 = UserFactory.create()
        self.project.add_member(user1, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user2, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user3, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])
        self.project.add_member(user4, role=self.project_role_member, badges=[ProjectMembership.BadgeType.QA])

        self.force_login(self.qa_member_user)

        # Create a commit
        _clear_notifications()
        minput = {
            'entry': self.entry.id,
            'text': 'This is a comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
            'mentionedUsers': [user2.pk],
        }
        # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            comment_id = self._query_check(minput, okay=True)['data']['project']['entryReviewCommentCreate']['result']['id']
        assert _get_comment_users_pk(comment_id) == set([user2.pk])
        assert _get_notifications_receivers() == (
            set([user2.pk]),
            set([Notification.Type.ENTRY_REVIEW_COMMENT_ADD]),
        )

        # Create a commit (multiple mentionedUsers)
        _clear_notifications()
        minput = {
            'entry': self.entry.id,
            'text': 'This is a comment',
            'commentType': self.genum(EntryReviewComment.CommentType.COMMENT),
            'mentionedUsers': [user2.pk, user3.pk, self.qa_member_user.pk],
        }
        # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            comment_id = self._query_check(minput, okay=True)['data']['project']['entryReviewCommentCreate']['result']['id']
        assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
        assert _get_notifications_receivers() == (
            set([user2.pk, user3.pk]),
            set([Notification.Type.ENTRY_REVIEW_COMMENT_ADD]),
        )

        # Create a commit different comment_type
        for comment_type in [
            EntryReviewComment.CommentType.VERIFY, EntryReviewComment.CommentType.UNVERIFY,
            EntryReviewComment.CommentType.CONTROL, EntryReviewComment.CommentType.UNCONTROL,
        ]:
            _clean_comments(self.project)
            _clear_notifications()
            minput = {
                'entry': self.entry.id,
                'text': 'This is a comment',
                'commentType': self.genum(comment_type),
                'mentionedUsers': [self.qa_member_user.pk, user2.pk, user3.pk],
            }
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                comment_id = self._query_check(
                    minput, okay=True)['data']['project']['entryReviewCommentCreate']['result']['id']
            assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
            assert _get_notifications_receivers() == (
                set([user2.pk, user3.pk]),
                set([Notification.Type.ENTRY_REVIEW_COMMENT_ADD]),
            )

            _clear_notifications()
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                self._query_check(minput, review_comment_id=comment_id, okay=True)
            assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
            assert _get_notifications_receivers() == (set(), set())  # No new notifications are created

            _clear_notifications()
            minput['text'] = 'this is a new comment text'
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                self._query_check(minput, review_comment_id=comment_id, okay=True)
            assert _get_comment_users_pk(comment_id) == set([user2.pk, user3.pk])
            assert _get_notifications_receivers() == (
                set([user2.pk, user3.pk]),
                set([Notification.Type.ENTRY_REVIEW_COMMENT_MODIFY]),
            )  # New notifications are created

            _clear_notifications()
            minput['mentionedUsers'].append(user4.pk)
            # Need self.captureOnCommitCallbacks as this API uses transation.on_commit
            with self.captureOnCommitCallbacks(execute=True):
                self._query_check(minput, review_comment_id=comment_id, okay=True)
            assert _get_comment_users_pk(comment_id) == set([user4.pk, user2.pk, user3.pk])
            assert _get_notifications_receivers() == (
                set([user4.pk]),
                set([Notification.Type.ENTRY_REVIEW_COMMENT_MODIFY]),
            )  # New notifications are created only for user2

    def test_entry_review_comment_delete(self):
        def _query_check(review_comment_id, **kwargs):
            variables = {'projectId': self.project.id, 'commentId': review_comment_id}
            return self.query_check(
                self.DELETE_ENTRY_REVIEW_COMMENT_QUERY,
                mnested=['project'],
                variables=variables,
                **kwargs
            )

        member_user2 = UserFactory.create()
        self.project.add_member(member_user2, role=self.project_role_member)
        create_kwargs = dict(entry=self.entry, created_by=member_user2)
        comments = [
            EntryReviewCommentFactory.create(comment_type=EntryReviewComment.CommentType.COMMENT, **create_kwargs)
            for comment_type in [
                EntryReviewComment.CommentType.VERIFY,
                EntryReviewComment.CommentType.UNVERIFY,
                EntryReviewComment.CommentType.CONTROL,
                EntryReviewComment.CommentType.UNCONTROL,
                EntryReviewComment.CommentType.COMMENT,
            ]
        ]

        # -- Without login
        [_query_check(comment.pk, assert_for_error=True) for comment in comments]

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        [_query_check(comment.pk, assert_for_error=True) for comment in comments]

        # -- With login (member but not creator)
        self.force_login(self.member_user)
        [_query_check(comment.pk, okay=False) for comment in comments]

        # -- With login (member but creator)
        self.force_login(member_user2)
        [
            (
                _query_check(comment.pk, okay=True) if comment.comment_type == EntryReviewComment.CommentType.COMMENT
                else _query_check(comment.pk, okay=False)
            )for index, comment in enumerate(comments)
        ]
