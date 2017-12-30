from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import TestCase
from gallery.tasks import extract_from_file
from os.path import join
from utils.common import (
    get_or_write_file,
    makedirs,
)
from utils.extractor.tests.test_file_document import DOCX_FILE

from gallery.models import File


class ExtractFromFileTaskTest(TestCase):
    """
    Test to test if the extract_from_file task works properly.

    Use a simple file stored in the repo to test this.
    """
    def setUp(self):
        # This is similar to test_file_document
        self.path = join(settings.TEST_DIR, 'documents_attachment')
        self.documents = join(settings.TEST_DIR, 'documents')
        makedirs(self.path)

        # Create the sample file
        self.file = File.objects.create(
            title='test',
            file=SimpleUploadedFile(
                name=DOCX_FILE,
                content=open(join(self.documents, DOCX_FILE), 'rb').read(),
            ),
        )

    def test_extraction(self):
        # Check if extraction works succesfully
        result = extract_from_file(self.file.id)
        self.assertTrue(result)

        # Check if the extraction did create proper file preview
        file_preview = self.file.filepreview
        self.assertIsNotNone(file_preview)

        # This is similar to test_file_document
        path = join(self.path, DOCX_FILE)
        extracted = get_or_write_file(path + '.txt', file_preview.text_extract)
        self.assertEqual(
            ' '.join(file_preview.text_extract.split()),
            ' '.join(extracted.read().split()),
        )
