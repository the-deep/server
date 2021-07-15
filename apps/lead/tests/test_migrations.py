import importlib

from deep.tests import TestCase

from lead.models import Lead
from ary.models import Assessment


class TestCustomMigrationsLogic(TestCase):
    """
    Test for the testing the custom migrations logic.
    Skip this test if the migration is removed.
    """

    def test_lead_is_assessment_migration(self):
        migration_file = importlib.import_module('lead.migrations.0037_auto_20210715_0432')

        lead_1 = self.create_lead()
        lead_2 = self.create_lead()
        lead_3 = self.create_lead()
        lead_4 = self.create_lead()

        self.create(Assessment, lead=lead_1)
        self.create(Assessment, lead=lead_2)
        self.create(Assessment, lead=lead_3)

        # Apply migration logic
        migration_file.set_lead_is_assessment_(Lead, Assessment)

        assert Lead.objects.count() == 4
        # should set the lead which have assesmment to `is_assessment_lead=True`
        assert set(
            Lead.objects.filter(is_assessment_lead=True)
        ) == set([lead_3, lead_1, lead_2])
        # check for the lead which has no any assessment created for
        assert set(Lead.objects.filter(id=lead_4.id).values_list('is_assessment_lead', flat=True)) == set([False])
