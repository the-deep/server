from os.path import join

from django.test import TestCase
from django.conf import settings

from utils.common import get_or_write_file
from ..extractors import (
    PdfStripper, DocxStripper, PptxStripper
)


class ExtractorTest(TestCase):
    """
    Import Test
    Pdf, Pptx and docx
    Note: Html test is in WebDocument Test
    """
    def setUp(self):
        self.path = join(settings.TEST_DIR, 'documents')

    def extract(self, extractor, path):
        text, images = extractor.simplify()
        extracted = get_or_write_file(path + '.txt', text)

        self.assertEqual(text, extracted.read())
        # TODO: Verify image
        # self.assertEqual(len(images), 4)

    def test_docx(self):
        """
        Test Docx import
        """
        docx_file = join(self.path, 'doc.docx')
        extractor = DocxStripper(open(docx_file, 'rb+'))
        self.extract(extractor, docx_file)

    def test_pptx(self):
        """
        Test pptx import
        """
        pptx_file = join(self.path, 'doc.pptx')
        extractor = PptxStripper(open(pptx_file, 'rb+'))
        self.extract(extractor, pptx_file)

    def test_pdf(self):
        """
        Test Pdf import
        """
        pdf_file = join(self.path, 'doc.pdf')
        extractor = PdfStripper(open(pdf_file, 'rb+'))
        self.extract(extractor, pdf_file)
