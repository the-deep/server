from os.path import (join, isfile)
import json
import logging

from django.test import TestCase
from django.conf import settings

from utils.common import (get_or_write_file, makedirs)
from ..file_document import FileDocument

# TODO: Review/Add better urls
DOCX_FILE = 'doc.docx'
PPTX_FILE = 'doc.pptx'
PDF_FILE = 'doc.pdf'

logger = logging.getLogger(__name__)


class FileDocumentTest(TestCase):
    """
    Import Test using files
    Html, Pdf, Pptx and docx
    """
    def setUp(self):
        self.path = join(settings.TEST_DIR, 'documents_attachment')
        self.documents = join(settings.TEST_DIR, 'documents')

        with open(join(self.documents, 'pages.json'), 'r') as pages:
            self.pages = json.load(pages)

        makedirs(self.path)

    def extract(self, path):
        file = open(join(self.documents, path), 'rb')
        filename = file.name.split('/')[-1]
        text, images, page_count = FileDocument(
            file,
            filename
        ).extract()
        path = join(self.path, filename)

        extracted = get_or_write_file(path + '.txt', text)

        self.assertEqual(text, extracted.read())
        self.assertEqual(page_count, self.pages[filename.split('.')[-1]])
        # TODO: Verify image
        # self.assertEqual(len(images), 4)

    def thumbnail(self, file_path):
        ERROR_TYPE = 'THUMBNAIL ERROR'
        doc = open(join(self.documents, file_path), 'rb')

        try:
            # thumbnail = FileDocument(
            FileDocument(
                doc,
                doc.name.split('/')[-1]
            ).get_thumbnail()
        except Exception:
            logger.warning('\n' + ('*' * 30))
            logger.warning('{}: FILEDOCUMENT: {}'.format(ERROR_TYPE, doc.name), exc_info=True)
            return

        # TODO: Thumbnail is a depricated feature. Remove this later
        # self.assertTrue(os.path.isfile(thumbnail.name))

    def test_docx(self):
        """
        Test Docx import
        """
        self.extract(DOCX_FILE)
        self.thumbnail(DOCX_FILE)

    def test_pptx(self):
        """
        Test pptx import
        """
        self.extract(PPTX_FILE)
        self.thumbnail(PPTX_FILE)

    def test_pdf(self):
        """
        Test Pdf import
        """
        self.extract(PDF_FILE)
        self.thumbnail(PDF_FILE)
