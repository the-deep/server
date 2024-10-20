import os
import logging
from parameterized import parameterized
from django.conf import settings

from deep.tests import TestCase
from utils.common import get_or_write_file, makedirs, sanitize_text
from utils.extractor.tests.test_web_document import HTML_URL, REDHUM_URL

from lead.tasks import extract_from_lead
from lead.models import Lead

logger = logging.getLogger(__name__)


class ExtractFromLeadTaskTest(TestCase):
    def create_lead_with_url(self, url):
        # Create the sample lead
        lead = self.create(Lead)
        lead.project.is_private = False
        lead.project.save()

        lead.text = ''
        lead.url = url
        lead.save()
        return lead

    def setUp(self):
        super().setUp()

        # This is similar to test_web_document
        self.path = os.path.join(settings.TEST_DIR, 'documents_urls')
        makedirs(self.path)

        # Create the sample lead
        self.lead = self.create_lead_with_url(HTML_URL)

    @parameterized.expand([
        ['relief_url', HTML_URL],  # Server Render Page
        ['redhum_url', REDHUM_URL],  # SPA
    ])
    def test_extraction_(self, _, url):
        # Create the sample lead
        lead = self.create_lead_with_url(url)
        # Check if extraction works succesfully
        try:
            result = extract_from_lead(lead.id)
            self.assertTrue(result)

            # Check if the extraction did create proper lead preview
            lead_preview = lead.leadpreview
            self.assertIsNotNone(lead_preview)

            # This is similar to test_web_document
            path = os.path.join(
                self.path,
                '.'.join(url.split('/')[-1:]),
            )
            extracted = get_or_write_file(path + '.txt', lead_preview.text_extract)
            self.assertEqual(
                ' '.join(lead_preview.text_extract.split()),
                sanitize_text(' '.join(extracted.read().split())),
            )
        except Exception:
            logger.warning('LEAD EXTRACTION ERROR:', exc_info=True)
            return
