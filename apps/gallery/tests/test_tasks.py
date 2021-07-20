from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import TestCase
from gallery.tasks import extract_from_file
from os.path import join
import logging

from utils.common import (
    get_or_write_file,
    makedirs,
)
from utils.extractor.tests.test_file_document import DOCX_FILE

from gallery.models import File, FilePreview

logger = logging.getLogger(__name__)


class ExtractFromFileTaskTest(TestCase):
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

        self.file_preview = FilePreview.objects.create(
            file_ids=[self.file.id],
            extracted=False,
        )

    def test_extraction(self):
        # TODO:
        print('SKIPING THIS AS WE ARE NOT USING DEEPL RIGHT NOW')
        return
        # Check if extraction works succesfully
        result = extract_from_file(self.file_preview.id)
        self.assertTrue(result)

        # Check if the extraction did occur
        self.file_preview = FilePreview.objects.get(id=self.file_preview.id)
        if not self.file_preview.extracted:
            border_len = 50
            logger.warning('*' * border_len)
            logger.warning('---- File extraction is not working ----')
            logger.warning('Probably an issue with DEEPL integration')
            logger.warning('*' * border_len)

        # This is similar to test_file_document
        path = join(self.path, DOCX_FILE)
        extracted = get_or_write_file(
            path + '.txt', self.file_preview.text
        )
        self.assertEqual(
            ' '.join(self.file_preview.text.split()),
            ' '.join(extracted.read().split()),
        )
