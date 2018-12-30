import os
from rest_framework.test import APITestCase
from autofixture.base import AutoFixture
from tempfile import NamedTemporaryFile

from django.conf import settings

from gallery.models import File
from geo.models import GeoArea

from tabular.tasks import auto_detect_and_update_fields
from tabular.extractor import csv
from tabular.models import Book, Field

consistent_csv_data = '''id,age,name,date,place
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,banana
1,10,john,2018 october 28,Kathmandu
abc,10,john,2018 october 28,mango
abc,30,doe,10 Nevem 2018,Kathmandu'''

inconsistent_csv_data = '''id,age,name,date,place
1,10,john,1994 December 29,Kathmandu
abc,10,john,1994 Deer 29,Kathmandu
1,10,john,199 Dmber 29,Kathmandu
1,10,john,1994 December 29,Kathmandu
abc,10,john,14 Dber 29,Kathmandu
abc,30,doe,10 Nevem 2018,Mango'''

geo_data_type_code = '''id,age,name,date,place
1,10,john,1994 December 29,KAT
abc,10,john,1994 Deer 29,KAT
1,10,john,199 Dmber 29,KAT
1,10,john,1994 December 29,KAT
abc,10,john,14 Dber 29,Kathmandu
abc,30,doe,10 Nevem 2018,Mango'''

geo_data_type_name = '''id,age,name,date,place
1,10,john,1994 December 29,KAT
abc,10,john,1994 Deer 29,Kathmandu
1,10,john,199 Dmber 29,KAT
1,10,john,1994 December 29,Kathmandu
abc,10,john,14 Dber 29,Kathmandu
abc,30,doe,10 Nevem 2018,Mango'''


class TestTabularExtraction(APITestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = []

    def setUp(self):
        Book.objects.all().delete()
        # geo_choices = ChoicesGenerator(values=areas)
        # NOTE: Using choices created random values, and thus error occured
        AutoFixture(
            GeoArea,
            field_values={
                'title': 'Kathmandu',
                'code': 'KAT'
            },
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
                assert field.options is None
            elif field.title == 'age':
                assert field.type == Field.NUMBER, 'age is number'
                assert field.options is None
            elif field.title == 'name':
                assert field.type == Field.STRING, 'name is string'
                assert field.options is None
            elif field.title == 'date':
                assert field.type == Field.DATETIME, 'date is datetime'
                assert field.options is None
            elif field.title == 'place':
                assert field.type == Field.GEO, 'place is geo'
                assert field.options is not None

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
                    'date is string: only less than 80% rows are of date type'
            elif field.title == 'place':
                assert field.type == Field.GEO,\
                    'place is geo: more than 80% rows are of geo type'

    def test_auto_detection_geo_type_name(self):
        """
        Testing geo type name
        """
        book = self.initialize_data_and_basic_test(geo_data_type_name)
        # now auto detect
        auto_detect_and_update_fields(book)

        sheets = book.sheet_set.all()
        for sheet in sheets:
            for row in sheet.data:
                for k, v in row.items():
                    if k == 'key':
                        continue
                    assert isinstance(v, dict)
                    assert 'value' in v
                    assert 'type' in v
                    assert v['type'] != Field.GEO or 'admin_level' in v
                    assert v['type'] != Field.GEO or 'geo_type' in v

        # now validate auto detected fields
        for field in Field.objects.all():
            if field.title == 'place':
                assert field.type == Field.GEO,\
                    'place is geo: more than 80% rows are of geo type'
                assert field.options != {}
                assert field.options['geo_type'] == 'name'
                assert 'admin_level' in field.options

    def test_auto_detection_geo_type_code(self):
        """
        Testing geo type code
        """
        book = self.initialize_data_and_basic_test(geo_data_type_code)
        # now auto detect
        auto_detect_and_update_fields(book)
        sheets = book.sheet_set.all()
        for sheet in sheets:
            for row in sheet.data:
                for k, v in row.items():
                    if k == 'key':
                        continue
                    assert isinstance(v, dict)
                    assert 'value' in v
                    assert 'type' in v
                    assert v['type'] != Field.GEO or 'admin_level' in v
                    assert v['type'] != Field.GEO or 'geo_type' in v

        # now validate auto detected fields
        for field in Field.objects.all():
            if field.title == 'place':
                assert field.type == Field.GEO,\
                    'place is geo: more than 80% rows are of geo type'
                assert field.options != {}
                assert field.options['geo_type'] == 'code'

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
