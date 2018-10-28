import os
from rest_framework.test import APITestCase
from autofixture.base import AutoFixture
from tempfile import NamedTemporaryFile

from django.conf import settings

from gallery.models import File

from .tasks import auto_detect_and_update_fields
from .extractor import csv
from .models import Book, Field

consistent_csv_data = '''id,age,address,date
1,10,chitwan,2018 october 28
2,30,kathmandu,10 Nov 2018'''

inconsistent_csv_data = '''id,age,address,date
1,10,chitwan,1994 December 29
abc,30,kathmandu,10 Nevem 2018'''


class TestTabularExtraction(APITestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = []

    def setUp(self):
        Book.objects.all().delete()

    def test_auto_detection_consistent(self):
        """
        Testing rows having consistent values
        """
        book = self.initialize_data_and_basic_test(consistent_csv_data)
        # now auto detect
        auto_detect_and_update_fields(book)

        # now validate auto detected fields
        for field in Field.objects.all():
            if field.title == 'id':
                assert field.type == Field.NUMBER, 'id is number'
            elif field.title == 'age':
                assert field.type == Field.NUMBER, 'age is number'
            elif field.title == 'address':
                assert field.type == Field.STRING, 'address is string'
            elif field.title == 'date':
                assert field.type == Field.DATETIME, 'date is datetime'

    def test_auto_detection_inconsistent(self):
        """
        Testing rows having inconsistent values
        """
        book = self.initialize_data_and_basic_test(inconsistent_csv_data)
        # now auto detect
        auto_detect_and_update_fields(book)

        # now validate auto detected fields
        for field in Field.objects.all():
            if field.title == 'id':
                assert field.type == Field.STRING,\
                    'id is string as it is inconsistent'
            elif field.title == 'age':
                assert field.type == Field.NUMBER, 'age is number'
            elif field.title == 'address':
                assert field.type == Field.STRING, 'address is string'
            elif field.title == 'date':
                assert field.type == Field.STRING,\
                    'date is string as it is inconsistent'

    def initialize_data_and_basic_test(self, csv_data):
        file = NamedTemporaryFile('w', dir=settings.MEDIA_ROOT, delete=False)

        self.files.append(file.name)

        for x in csv_data.split('\n'):
            file.write('{}\n'.format(x))
        file.close()
        # create a book
        csvfile = AutoFixture(
            File,
            field_values={
                'file': file.name
            }
        ).create_one()
        book = AutoFixture(
            Book,
            field_values={
                'file': csvfile
            }
        ).create_one()
        csv.extract(book)
        assert Field.objects.count() == 4
        fieldnames = {}
        for field in Field.objects.all():
            fieldnames[field.title] = True
            assert field.type == Field.STRING, "Initial type is string"
        assert 'id' in fieldnames, 'id should be a fieldname'
        assert 'age' in fieldnames, 'age should be a fieldname'
        assert 'address' in fieldnames, 'address should be a field name'
        assert 'date' in fieldnames, 'date should be a field name'

        return book

    def tearDown(self):
        """Remove temp files"""
        for file in self.files:
            os.remove(file)
