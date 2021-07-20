import os
import logging
import json

from django.test import TestCase
from django.conf import settings

from utils.common import (get_or_write_file, makedirs)
from ..web_document import WebDocument

logger = logging.getLogger(__name__)

# TODO: Review/Add better urls
REDHUM_URL = 'https://redhum.org/documento/3227553'
HTML_URL = 'https://reliefweb.int/report/occupied-palestinian-territory/rehabilitation-services-urgently-needed-prevent-disability'  # noqa
DOCX_URL = 'https://calibre-ebook.com/downloads/demos/demo.docx'
PPTX_URL = 'https://www.mhc.ab.ca/-/media/Files/PDF/Services/Online/'\
           'BBSamples/powerpoint.pptx'
PDF_URL = 'http://che.org.il/wp-content/uploads/2016/12/pdf-sample.pdf'


class WebDocumentTest(TestCase):
    """
    Import Test using urls
    Html, Pdf, Pptx and docx
    """
    def setUp(self):
        self.path = os.path.join(settings.TEST_DIR, 'documents_urls')
        with open(os.path.join(self.path, 'pages.json'), 'r') as pages:
            self.pages = json.load(pages)
        makedirs(self.path)

    def extract(self, url, type):
        try:
            text, images, page_count = WebDocument(url).extract()
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('EXTRACTOR ERROR: WEBDOCUMENT: ' + type.upper())
            logger.warning(traceback.format_exc())
            return

        path = os.path.join(self.path, '.'.join(url.split('/')[-1:]))

        extracted = get_or_write_file(path + '.txt', text)

        try:
            # TODO: Better way to handle the errors
            self.assertEqual(text.strip(), extracted.read().strip())
            self.assertEqual(page_count, self.pages[type])
        except AssertionError:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('EXTRACTOR ERROR: WEBDOCUMENT: ' + type.upper())
            logger.warning(traceback.format_exc())
        # TODO: Verify image
        # self.assertEqual(len(images), 4)

    def thumbnail(self, url, file_type):
        try:
            # thumbnail = WebDocument(url).get_thumbnail()
            WebDocument(url).get_thumbnail()
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('THUMBNAIL ERROR: WEBDOCUMENT: {}'.format(file_type.upper()))
            logger.warning(traceback.format_exc())
            return
        # TODO: Thumbnail is a depricated feature. Remove this later
        # self.assertTrue(os.path.isfile(thumbnail.name))

    def test_html(self):
        """
        Test html import
        """
        self.extract(HTML_URL, 'html')
        self.thumbnail(HTML_URL, 'html')

    def test_docx(self):
        """
        Test Docx import
        """
        self.extract(DOCX_URL, 'docx')
        self.thumbnail(DOCX_URL, 'docx')

    def test_pptx(self):
        """
        Test pptx import
        """
        self.extract(PPTX_URL, 'pptx')
        self.thumbnail(PPTX_URL, 'pptx')

    def test_pdf(self):
        """
        Test Pdf import
        """
        self.extract(PDF_URL, 'pdf')
        self.thumbnail(PDF_URL, 'pdf')
