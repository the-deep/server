from django.conf import settings
from django.test import TestCase
from lead.tasks import extract_from_lead
from os.path import join
from utils.common import (
    get_or_write_file,
    makedirs,
)
from utils.extractor.tests.test_web_document import HTML_URL

from lead.tests.test_apis import LeadMixin
from project.tests.test_apis import ProjectMixin


class ExtractFromLeadTaskTest(ProjectMixin, LeadMixin, TestCase):
    """
    Test to test if the extract_from_lead task works properly.

    Use a simple lead with a html url to test this.
    """
    def setUp(self):
        # This is similar to test_web_document
        self.path = join(settings.TEST_DIR, 'documents_urls')
        makedirs(self.path)

        # Create the sample lead
        self.user = None
        self.lead = self.create_or_get_lead()
        self.lead.text = ''
        self.lead.url = HTML_URL
        self.lead.save()

    def test_extraction(self):
        # Check if extraction works succesfully
        result = extract_from_lead(self.lead.id)
        self.assertTrue(result)

        # Check if the extraction did create proper lead preview
        lead_preview = self.lead.leadpreview
        self.assertIsNotNone(lead_preview)

        # This is similar to test_web_document
        path = join(self.path, '.'.join(HTML_URL.split('/')[-1:]))
        extracted = get_or_write_file(path + '.txt', lead_preview.text_extract)
        self.assertEqual(lead_preview.text_extract, extracted.read())
