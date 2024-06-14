import json
import logging
from os.path import join  # isfile,

from django.conf import settings
from django.test import TestCase

from utils.common import get_or_write_file, makedirs

from ..file_document import FileDocument

# TODO: Review/Add better urls
DOCX_FILE = "doc.docx"
PPTX_FILE = "doc.pptx"
PDF_FILE = "doc.pdf"

logger = logging.getLogger(__name__)


class FileDocumentTest(TestCase):
    """
    Import Test using files
    Html, Pdf, Pptx and docx
    """

    def setUp(self):
        self.path = join(settings.TEST_DIR, "documents_attachment")
        self.documents = join(settings.TEST_DIR, "documents")

        with open(join(self.documents, "pages.json"), "r") as pages:
            self.pages = json.load(pages)

        makedirs(self.path)

    def extract(self, path):
        file = open(join(self.documents, path), "rb")
        filename = file.name.split("/")[-1]
        text, images, page_count = FileDocument(file, filename).extract()
        path = join(self.path, filename)

        extracted = get_or_write_file(path + ".txt", text)

        self.assertEqual(text, extracted.read())
        self.assertEqual(page_count, self.pages[filename.split(".")[-1]])
        # TODO: Verify image
        # self.assertEqual(len(images), 4)

    def test_docx(self):
        """
        Test Docx import
        """
        self.extract(DOCX_FILE)

    def test_pptx(self):
        """
        Test pptx import
        """
        self.extract(PPTX_FILE)

    def test_pdf(self):
        """
        Test Pdf import
        """
        self.extract(PDF_FILE)
