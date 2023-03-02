import pytest
from unittest.mock import patch
from django.db.models import Q

from deep.tests import TestCase
from project.factories import ProjectFactory
from lead.factories import LeadPreviewFactory, LeadFactory
from lead.receivers import update_index_and_duplicates
from lead.models import Lead, LeadDuplicates
from deduplication.models import LSHIndex
from deduplication.factories import LSHIndexFactory
from deduplication.tasks.indexing import (
    process_and_index_lead,
    get_index_object_for_project,
    index_lead_and_calculate_duplicates,
    remove_lead_from_index,
    create_project_index,
)


@pytest.mark.django_db
class TestTasks(TestCase):
    """
    Unit tests for the tasks in deduplication module
    """

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()

    def test_get_index_object_for_project_new(self):
        """Test get index object when there is no index object for project"""
        original_count = LSHIndex.objects.count()
        index_obj = get_index_object_for_project(self.project)
        assert index_obj is not None
        final_count = LSHIndex.objects.count()
        assert final_count == original_count + 1, "One LSHIndex should be created"

    def test_get_index_object_for_project_existing(self):
        """Test get index object when there is an existing index object for project"""
        LSHIndexFactory.create(project=self.project)
        index_obj = get_index_object_for_project(self.project)
        original_count = LSHIndex.objects.count()
        assert index_obj is not None
        final_count = LSHIndex.objects.count()
        assert final_count == original_count

    @patch('deduplication.tasks.indexing.get_index_object_for_project')
    def test_index_lead_and_calculate_duplicates_no_text(self, get_index_func):
        """When lead has no text, the function should return early without calling
        the function get_index_object_for_project
        """
        lead = LeadFactory.create(text="")
        LeadPreviewFactory.create(lead=lead, text_extract="")
        index_lead_and_calculate_duplicates(lead.id)
        get_index_func.assert_not_called()

    @patch('deduplication.tasks.indexing.process_and_index_lead')
    def test_index_lead_and_calculate_duplicates_errored_index(self, process_lead_func):
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LSHIndexFactory.create(project=project, has_errored=True)
        index_lead_and_calculate_duplicates(lead.id)
        process_lead_func.assert_not_called()

    def test_index_lead_and_calculate_duplicates(self):
        """Test indexing of lead"""
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LeadPreviewFactory.create(lead=lead, text_extract="This is some text")
        index_lead_and_calculate_duplicates(lead.id)

        # get LSHIndex object
        index_obj = LSHIndex.objects.get(project=project)
        assert lead.id in index_obj.index, "Lead should be present in the key"

    def test_process_and_index_lead(self):
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LeadPreviewFactory.create(lead=lead, text_extract="This is some text")
        index_obj = get_index_object_for_project(project)
        process_and_index_lead(lead, index_obj.index)
        assert lead.is_indexed is True
        assert lead.indexed_at is not None

        assert index_obj.index is not None
        assert lead.id in index_obj.index

    def test_find_and_set_duplicate_leads(self):
        project = ProjectFactory.create()
        [lead1, lead2] = LeadFactory.create_batch(2, project=project)
        # Create lead previews with same conent
        common_text = "This is a common text between two leads. The purpose is to mark them as duplicates"
        LeadPreviewFactory.create(lead=lead1, text_extract=common_text)
        # Have same text so that, they will be marked as duplicates
        LeadPreviewFactory.create(lead=lead2, text_extract=common_text)
        assert list(lead1.duplicate_leads.all()) == [], "No duplicates for lead1 in the beginning"
        assert list(lead2.duplicate_leads.all()) == [], "No duplicates for lead2 in the beginning"

        # Index lead1, at this point there should be no duplicates for it
        index_lead_and_calculate_duplicates(lead1.id)

        # Index lead2, at this point, lead1 should be marked its duplicate
        index_lead_and_calculate_duplicates(lead2.id)
        assert lead2.duplicate_leads is not None

        # Also has_duplicates of both the leads should be true
        lead1 = Lead.objects.get(pk=lead1.id)
        lead2 = Lead.objects.get(pk=lead2.id)
        assert lead1.is_indexed is True
        assert lead2.is_indexed is True
        assert lead1.duplicate_leads_count == 1
        assert lead2.duplicate_leads_count == 1

    def test_remove_lead_from_index(self):
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LeadPreviewFactory.create(lead=lead, text_extract="This is some text")
        index_lead_and_calculate_duplicates(lead.id)
        index_obj = get_index_object_for_project(project)
        assert lead.id in index_obj.index, "The lead should be present in index"
        # Now remove lead
        remove_lead_from_index(lead.id)
        index_obj = get_index_object_for_project(project)
        assert lead.id not in index_obj.index, "The lead should be removed in index"

    def test_remove_lead_index_object(self):
        project = ProjectFactory.create()
        num_leads = 3
        leads = LeadFactory.create_batch(num_leads, project=project)
        # Create lead previews with same conent
        common_text = "This is a common text between two leads. The purpose is to mark them as duplicates"
        for lead in leads:
            # Have same text so that, they will be marked as duplicates
            LeadPreviewFactory.create(lead=lead, text_extract=common_text)

        assert LSHIndex.objects.count() == 0, "No index should be created"
        assert LeadDuplicates.objects.all().count() == 0, "No duplicates"
        assert Lead.objects.filter(project=project, is_indexed=True).count() == 0, "No leads are indexed"

        # Create index
        create_project_index(project)
        assert LSHIndex.objects.count() == 1, "An index should be created"

        assert LeadDuplicates.objects.all().count() > 0, "Duplicates should be created"

        project_leads_qs = Lead.objects.filter(project=project)
        indexed_leads_qs = project_leads_qs.filter(is_indexed=True)
        assert indexed_leads_qs.count() == num_leads, "Leads must be indexed"

        leads_with_duplicates = project_leads_qs.filter(duplicate_leads_count__gt=0)
        assert leads_with_duplicates.count() == num_leads, "All leads should have duplicates"

        # Delete index object
        with self.captureOnCommitCallbacks(execute=True):
            LSHIndex.objects.filter(project=project).delete()

        project_leads = Lead.objects.filter(project=project)
        assert project_leads.filter(is_indexed=True).count() == 0, "No leads should be indexed"
        assert project_leads.filter(duplicate_leads_count__gt=0).count() == 0, "No leads should have duplicates"
        assert LeadDuplicates.objects.all().count() == 0

    def test_update_index_and_duplicates(self):
        project = ProjectFactory.create()
        num_leads = 3
        leads = LeadFactory.create_batch(num_leads, project=project)
        first_lead = leads[0]

        # Create lead previews with same conent
        common_text = "This is a common text between two leads. The purpose is to mark them as duplicates"
        for lead in leads:
            # Have same text so that, they will be marked as duplicates
            LeadPreviewFactory.create(lead=lead, text_extract=common_text)

        create_project_index(project)

        # Refresh lead objects
        for lead in leads:
            lead.refresh_from_db()

        project_leads = Lead.objects.filter(project=project)
        assert project_leads.filter(duplicate_leads_count=0).count() == 0, "Leads should have duplicates"
        assert LeadDuplicates.objects.filter(
            Q(source_lead_id=first_lead.id) |
            Q(target_lead_id=first_lead.id)
        ).count() > 0, "There should be duplicates entries for the first lead"

        # NOTE: this should have been called by signal
        update_index_and_duplicates(first_lead)

        # Check for new duplicate_leads_count
        for lead_ in leads[1:]:
            original_count = lead_.duplicate_leads_count
            lead_.refresh_from_db()
            lead = Lead.objects.get(id=lead_.id)
            assert lead.duplicate_leads_count == original_count - 1
