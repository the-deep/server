import os
from rest_framework.test import APITestCase
from autofixture.base import AutoFixture
from autofixture.generators import ChoicesGenerator
from tempfile import NamedTemporaryFile

from django.conf import settings

from gallery.models import File
from geo.models import GeoArea

from .tasks import auto_detect_and_update_fields
from .extractor import csv
from .models import Book, Field

consistent_csv_data = '''id,age,name,date,place
1,10,john,2018 october 28,Kathmandu
2,30,doe,10 Nov 2018,Chitwan'''

inconsistent_csv_data = '''id,age,name,date,place
1,10,john,1994 December 29,Kathmandu
abc,30,doe,10 Nevem 2018,Mango'''


class TestTabularExtraction(APITestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = []

    def setUp(self):
        Book.objects.all().delete()
        areas = ['Kathmandu', 'Chitwan']
        geochoices = ChoicesGenerator(values=areas)
        AutoFixture(
            GeoArea,
            field_values={'title': geochoices},
            generate_fk=True
        ).create(3)

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
            elif field.title == 'name':
                assert field.type == Field.STRING, 'name is string'
            elif field.title == 'date':
                assert field.type == Field.DATETIME, 'date is datetime'
            elif field.title == 'place':
                assert field.type == Field.GEO, 'place is geo'

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
            elif field.title == 'name':
                assert field.type == Field.STRING, 'name is string'
            elif field.title == 'date':
                assert field.type == Field.STRING,\
                    'date is string as it is inconsistent'
            elif field.title == 'place':
                assert field.type == Field.STRING,\
                    'place is string as it is inconsistent'

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
        assert Field.objects.count() == 5
        fieldnames = {}
        for field in Field.objects.all():
            fieldnames[field.title] = True
            assert field.type == Field.STRING, "Initial type is string"
        assert 'id' in fieldnames, 'id should be a fieldname'
        assert 'age' in fieldnames, 'age should be a fieldname'
        assert 'name' in fieldnames, 'name should be a field name'
        assert 'date' in fieldnames, 'date should be a field name'
        assert 'place' in fieldnames, 'place should be a field name'

        return book

    def tearDown(self):
        """Remove temp files"""
        for file in self.files:
            os.remove(file)
