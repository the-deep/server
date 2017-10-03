from os.path import join

from django.test import TestCase
from django.conf import settings

from utils.common import (get_or_write_file, makedirs)
from ..file_document import FileDocument

# TODO: Review/Add better urls
DOCX_FILE = 'doc.docx'
PPTX_FILE = 'doc.pptx'
PDF_FILE = 'doc.pdf'


class FileDocumentTest(TestCase):
    """
    Import Test using files
    Html, Pdf, Pptx and docx
    """
    def setUp(self):
        self.path = join(settings.TEST_DIR, 'documents_attachment')
        self.documents = join(settings.TEST_DIR, 'documents')
        makedirs(self.path)

    def extract(self, path):
        file = open(join(self.documents, path), 'rb')
        text, images = FileDocument(
            file,
            file.name.split('/')[-1]
        ).extract()
        path = join(self.path, file.name.split('/')[-1])

        extracted = get_or_write_file(path + '.txt', text)

        self.assertEqual(text, extracted.read())
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
