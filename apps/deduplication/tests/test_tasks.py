import pytest
from unittest import TestCase
from unittest.mock import patch

from project.factories import ProjectFactory
from lead.factories import LeadPreviewFactory, LeadFactory
from deduplication.models import LSHIndex
from deduplication.factories import LSHIndexFactory
from deduplication.tasks.indexing import (
    process_and_index_lead,
    get_index_object_for_project,
    index_lead_and_calculate_duplicates,
    remove_lead_from_index,
)


@pytest.mark.django_db
class TestTasks(TestCase):
    """
    Unit tests for the tasks in deduplication module
    """

    def setUp(self):
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
        LSHIndexFactory.create()
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
        lead = LeadFactory.create()
        LeadPreviewFactory.create(lead=lead, text_extract="")
        index_lead_and_calculate_duplicates(lead)
        get_index_func.assert_not_called()

    @patch('deduplication.tasks.indexing.process_and_index_lead')
    def test_index_lead_and_calculate_duplicates_errored_index(self, process_lead_func):
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LSHIndexFactory.create(project=project, has_errored=True)
        index_lead_and_calculate_duplicates(lead)
        process_lead_func.assert_not_called()

    def test_index_lead_and_calculate_duplicates(self):
        """Test indexing of lead"""
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LeadPreviewFactory.create(lead=lead, text_extract="This is some text")
        index_lead_and_calculate_duplicates(lead)

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
        lead1 = LeadFactory.create(project=project)
        lead2 = LeadFactory.create(project=project)
        print('lead1 dupilcates', lead1.duplicate_leads)
        # Create lead previews with same conent
        common_text = "This is a common text between two leads. The purpose is to mark them as duplicates"
        LeadPreviewFactory.create(lead=lead1, text_extract=common_text)
        LeadPreviewFactory.create(lead=lead2, text_extract=common_text)
        assert list(lead1.duplicate_leads.all()) == [], "No duplicates for lead1 in the beginning"
        assert list(lead2.duplicate_leads.all()) == [], "No duplicates for lead2 in the beginning"

        # Index lead1, at this point there should be no duplicates for it
        index_lead_and_calculate_duplicates(lead1)

        # Index lead2, at this point, lead1 should be marked its duplicate
        index_lead_and_calculate_duplicates(lead2)
        assert lead2.duplicate_leads is not None

    def test_remove_lead_from_index(self):
        project = ProjectFactory.create()
        lead = LeadFactory.create(project=project)
        LeadPreviewFactory.create(lead=lead, text_extract="This is some text")
        index_lead_and_calculate_duplicates(lead)
        index_obj = get_index_object_for_project(project)
        assert lead.id in index_obj.index, "The lead should be present in index"
        # Now remove lead
        remove_lead_from_index(lead)
        index_obj = get_index_object_for_project(project)
        assert lead.id not in index_obj.index, "The lead should be removed in index"
