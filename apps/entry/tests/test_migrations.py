import importlib

from deep.tests import TestCase

from entry.models import Entry
from quality_assurance.models import EntryReviewComment, CommentType


class TestCustomMigrationsLogic(TestCase):
    """
    This test are for testing the custom logic used during migration.
    We can skip this test if the migration is done as it doesn't need to be maintain in future.
    TODO: Better way?
    """

    def test_test_entry_review_verify_control_migrations(self):
        migration_file = importlib.import_module('entry.migrations.0031_entry-migrate-verify-to-review-comment')

        user1 = self.create_user(
            username='jon1@dave.com',
            email='jon1@dave.com',
            password='test',
        )
        user2 = self.create_user(
            username='jon2@dave.com',
            email='jon2@dave.com',
            password='test',
        )
        user3 = self.create_user(
            username='jon3@dave.com',
            email='jon3@dave.com',
            password='test',
        )
        # Additional non-active user
        self.create_user(username='jon4@dave.com', email='jon3@dave.com', password='test')

        # Create entry before data migrate
        self.create_entry(controlled=True, controlled_changed_by=user1)
        self.create_entry(controlled=True, controlled_changed_by=user2)
        self.create_entry(controlled=False, controlled_changed_by=user3)
        self.create_entry(controlled=True, controlled_changed_by=None)
        self.create_entry(controlled=False, controlled_changed_by=None)

        # Apply the migration logic
        migration_file.migrate_entry_controlled_to_review_comment_(Entry, EntryReviewComment)

        assert Entry.objects.count() == 5
        # 2 verified review comment are created and 1 unverified review comment is created
        assert EntryReviewComment.objects.count() == 3
        # Related review comment are created by user last action on entry.
        assert set(EntryReviewComment.objects.values_list('created_by_id', flat=True)) == set([user1.pk, user2.pk, user3.pk])
        assert EntryReviewComment.objects.filter(comment_type=CommentType.VERIFY).count() == 2
        assert EntryReviewComment.objects.filter(comment_type=CommentType.UNVERIFY).count() == 1
        assert set(
            EntryReviewComment.objects.filter(comment_type=CommentType.VERIFY).values_list('created_by_id', flat=True)
        ) == set([user1.pk, user2.pk])
        assert set(
            EntryReviewComment.objects.filter(comment_type=CommentType.UNVERIFY).values_list('created_by_id', flat=True)
        ) == set([user3.pk])
        # All controlled, controlled_changed_by should be reset.
        assert Entry.objects.filter(controlled=True).count() == 0
        assert Entry.objects.filter(controlled_changed_by__isnull=False).count() == 0
