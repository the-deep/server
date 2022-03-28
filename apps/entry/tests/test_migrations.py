import importlib

from django.db import models
from deep.tests import TestCase

from entry.models import Entry
from quality_assurance.models import EntryReviewComment

from project.factories import ProjectFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from user.factories import UserFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory


class TestCustomMigrationsLogic(TestCase):
    """
    This test are for testing the custom logic used during migration.
    We can skip this test if the migration is done as it doesn't need to be maintain in future.
    TODO: Better way?
    """

    def test_test_entry_review_verify_control_migrations(self):
        migration_file = importlib.import_module('entry.migrations.0031_entry-migrate-verify-to-review-comment')

        # 3 normal users + Additional non-active user
        user1, user2, user3, _ = UserFactory.create_batch(4)

        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        lead = LeadFactory.create(project=project)

        # Create entry before data migrate
        EntryFactory.create(lead=lead, controlled=True, controlled_changed_by=user1)
        EntryFactory.create(lead=lead, controlled=True, controlled_changed_by=user2)
        EntryFactory.create(lead=lead, controlled=False, controlled_changed_by=user3)
        EntryFactory.create(lead=lead, controlled=True, controlled_changed_by=None)
        EntryFactory.create(lead=lead, controlled=False, controlled_changed_by=None)

        # Apply the migration logic
        migration_file.migrate_entry_controlled_to_review_comment_(Entry, EntryReviewComment)

        assert Entry.objects.count() == 5
        # 2 verified review comment are created and 1 unverified review comment is created
        assert EntryReviewComment.objects.count() == 3
        # Related review comment are created by user last action on entry.
        assert set(EntryReviewComment.objects.values_list('created_by_id', flat=True)) == set([user1.pk, user2.pk, user3.pk])
        assert EntryReviewComment.objects.filter(comment_type=EntryReviewComment.CommentType.VERIFY).count() == 2
        assert EntryReviewComment.objects.filter(comment_type=EntryReviewComment.CommentType.UNVERIFY).count() == 1
        assert set(
            EntryReviewComment.objects.filter(
                comment_type=EntryReviewComment.CommentType.VERIFY,
            ).values_list('created_by_id', flat=True)
        ) == set([user1.pk, user2.pk])
        assert set(
            EntryReviewComment.objects.filter(
                comment_type=EntryReviewComment.CommentType.UNVERIFY,
            ).values_list('created_by_id', flat=True)
        ) == set([user3.pk])
        # All controlled, controlled_changed_by should be reset.
        assert Entry.objects.filter(controlled=True).count() == 0
        assert Entry.objects.filter(controlled_changed_by__isnull=False).count() == 0

    def test_entry_dropped_excerpt_migrations(self):
        def _get_excerpt_snapshot():
            return list(Entry.objects.order_by('id').values_list('excerpt', 'dropped_excerpt', 'excerpt_modified'))

        migration_file = importlib.import_module('entry.migrations.0036_entry_excerpt_modified')

        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        lead = LeadFactory.create(project=project)

        # Create entry before data migrate
        EntryFactory.create(lead=lead, excerpt='', dropped_excerpt='')
        EntryFactory.create(lead=lead, excerpt='sample-1', dropped_excerpt='')
        EntryFactory.create(lead=lead, excerpt='sample-2', dropped_excerpt='sample-2-updated')
        EntryFactory.create(lead=lead, excerpt='sample-3', dropped_excerpt='sample-3')
        old_excerpt_snaphost = _get_excerpt_snapshot()

        # Apply the migration logic
        migration_file._update_entry_excerpt(Entry)
        new_excerpt_snaphost = _get_excerpt_snapshot()

        assert Entry.objects.count() == 4
        assert Entry.objects.filter(dropped_excerpt='').count() == 1
        assert Entry.objects.filter(excerpt_modified=True).count() == 1
        assert Entry.objects.filter(dropped_excerpt=models.F('excerpt')).count() == 3
        assert Entry.objects.exclude(dropped_excerpt=models.F('excerpt')).count() == 1

        assert new_excerpt_snaphost != old_excerpt_snaphost
        assert new_excerpt_snaphost == [
            ('', '', False),
            ('sample-1', 'sample-1', False),
            ('sample-2', 'sample-2-updated', True),
            ('sample-3', 'sample-3', False),
        ]
