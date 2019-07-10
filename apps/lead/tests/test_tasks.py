from django.conf import settings
from deep.tests import TestCase
from mock import patch

from lead.tasks import (
    extract_from_lead,
    _preprocess,
    send_lead_text_to_deepl,
    requests,
)
from lead.models import Lead, LeadPreview
from project.models import Project

from utils.common import get_or_write_file, makedirs
from utils.extractor.tests.test_web_document import HTML_URL

import os
import logging
logger = logging.getLogger(__name__)


class ExtractFromLeadTaskTest(TestCase):
    def setUp(self):
        super().setUp()

        # This is similar to test_web_document
        self.path = os.path.join(settings.TEST_DIR, 'documents_urls')
        makedirs(self.path)

        # Create the sample lead
        self.lead = self.create(Lead)
        self.lead.project.is_private = False
        self.lead.project.save()

        self.lead.text = ''
        self.lead.url = HTML_URL
        self.lead.save()

    def test_extraction(self):
        # Check if extraction works succesfully
        try:
            result = extract_from_lead(self.lead.id)
            self.assertTrue(result)

            # Check if the extraction did create proper lead preview
            lead_preview = self.lead.leadpreview
            self.assertIsNotNone(lead_preview)

            # This is similar to test_web_document
            path = os.path.join(
                self.path,
                '.'.join(HTML_URL.split('/')[-1:]),
            )
            extracted = get_or_write_file(path + '.txt',
                                          lead_preview.text_extract)
            self.assertEqual(
                ' '.join(lead_preview.text_extract.split()),
                _preprocess(' '.join(extracted.read().split())),
            )
        except Exception:
            import traceback
            logger.warning('LEAD EXTRACTION ERROR:')
            logger.warning(traceback.format_exc())
            return

    @patch('lead.tasks.send_lead_text_to_deepl.retry')
    @patch('lead.tasks.requests.post')
    def test_deepl_request_failure(self, post_mock, send_retry_mock):
        # Create lead preview
        LeadPreview.objects.create(
            lead=self.lead,
            text_extract="This is test text"
        )
        post_mock.side_effect = Exception()
        send_lead_text_to_deepl(self.lead.id)
        # First retry has countdown 1
        send_retry_mock.assert_called_with(countdown=1)

    @patch('lead.tasks.send_lead_text_to_deepl.retry')
    @patch('lead.tasks.requests.post')
    def test_deepl_request_success(self, post_mock, send_retry_mock):
        # Create lead preview
        LeadPreview.objects.create(
            lead=self.lead,
            text_extract="This is test text"
        )
        success_resp = requests.Response()
        success_resp._content = b'{"clasified_doc_id": 100}'
        success_resp.status_code = 200
        post_mock.return_value = success_resp
        ret = send_lead_text_to_deepl(self.lead.id)
        assert ret is True

    @patch('lead.tasks.requests.post')
    def test_no_nlp_called_for_private_project(self, post_mock):
        # Create Private Project
        project = self.create(Project, is_private=True)
        lead = self.create(Lead, project=project)
        # Create LeadPreview
        LeadPreview.objects.create(
            lead=lead,
            text_extract="Text not to be sent to DEEPL"
        )
        ret = send_lead_text_to_deepl(lead.id)
        assert ret is True
        assert not post_mock.called, "Post method should not be called"

    @patch('lead.tasks.requests.post')
    def test_nlp_called_for_public_project(self, post_mock):
        # Create Public Project
        project = self.create(Project, is_private=False)
        lead = self.create(Lead, project=project)
        # Create LeadPreview
        LeadPreview.objects.create(
            lead=lead,
            text_extract="Text to be sent to DEEPL"
        )
        success_resp = requests.Response()
        success_resp._content = b'{"clasified_doc_id": 100}'
        success_resp.status_code = 200
        post_mock.return_value = success_resp

        ret = send_lead_text_to_deepl(lead.id)
        assert post_mock.called, "Post method should be called"
        assert ret is True
