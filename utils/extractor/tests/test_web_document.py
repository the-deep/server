from os.path import join

from django.test import TestCase
from django.conf import settings

from utils.common import (get_or_write_file, makedirs)
from ..web_document import WebDocument

# TODO: Review/Add better urls
HTML_URL = 'https://www.reddit.com'
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
        self.path = join(settings.TEST_DIR, 'documents_urls')
        makedirs(self.path)

    def extract(self, url):
        text, images = WebDocument(url).extract()
        path = join(self.path, '.'.join(url.split('/')[-1:]))

        extracted = get_or_write_file(path + '.txt', text)

        self.assertEqual(text, extracted.read())
        # TODO: Verify image
        # self.assertEqual(len(images), 4)

    def test_html(self):
        """
        Test html import
        """
        self.extract(HTML_URL)

    def test_docx(self):
        """
        Test Docx import
        """
        self.extract(DOCX_URL)

    def test_pptx(self):
        """
        Test pptx import
        """
        self.extract(PPTX_URL)

    def test_pdf(self):
        """
        Test Pdf import
        """
        self.extract(PDF_URL)
