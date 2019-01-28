import os
from functools import reduce
from rest_framework.test import APITestCase
from autofixture.base import AutoFixture
from tempfile import NamedTemporaryFile

from django.conf import settings

from gallery.models import File
from geo.models import GeoArea

from tabular.tasks import auto_detect_and_update_fields
from tabular.extractor import csv
from tabular.models import Book, Field, Sheet

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
a,10,john,199 Dmber 29,Kathmandu
1,10,john,1994 December 29,Kathmandu
abc,10,john,14 Dber 29,Kathmandu
abc,30,doe,10 Nevem 2018,Mango'''

geo_data_type_code = '''id,age,name,date,place
1,10,john,1994 December 29,KAT
abc,10,john,1994 Deer 29,KAT
1,10,john,199 Dmber 29,KAT
1,10,john,1994 December 29,KAT
abc,10,john,14 Dber 29, KAT
abc,30,doe,10 Nevem 2018,KAT'''

geo_data_type_name = '''id,age,name,date,place
1,10,john,1994 December 29,Kathmandu
abc,10,john,1994 Deer 29,Kathmandu
1,10,john,199 Dmber 29,Kathmandu
1,10,john,1994 December 29,Kathmandu
abc,10,john,14 Dber 29,Kathmandu
abc,30,doe,10 Nevem 2018,Kathmandu'''


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
        ).create(1)

    def test_auto_detection_consistent(self):
        """
        Testing rows having consistent values
        """
        book = self.initialize_data_and_basic_test(consistent_csv_data)
        # now auto detect
        auto_detect_and_update_fields(book)

        # Check for sheet invalid/empty values
        sheet = Sheet.objects.last()
        data = sheet.data

        assert 'columns' in data
        columns = data['columns']

        assert 'invalid_values' in data
        invalid_values = data['invalid_values']

        assert 'empty_values' in data
        empty_values = data['empty_values']

        # now validate auto detected fields
        for field in Field.objects.filter(sheet=sheet):
            fid = str(field.pk)
            assert len(columns[fid]) == 10

            if field.title == 'id':
                assert field.type == Field.NUMBER, 'id is number'
                assert invalid_values[fid] == [8, 9]
            elif field.title == 'age':
                assert field.type == Field.NUMBER, 'age is number'
            elif field.title == 'name':
                assert field.type == Field.STRING, 'name is string'
            elif field.title == 'date':
                assert field.type == Field.DATETIME, 'date is datetime'
                assert field.options is not None
                assert 'date_format' in field.options
                assert invalid_values[fid] == [9]
            elif field.title == 'place':
                assert field.type == Field.GEO, 'place is geo'
                assert field.options is not None
                assert invalid_values[fid] == [6, 8]
                assert empty_values[fid] == []

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

        # now validate auto detected fields
        geofield = None
        for field in Field.objects.all():
            if field.title == 'place':
                geofield = field
                assert field.type == Field.GEO,\
                    'place is geo: more than 80% rows are of geo type'
                assert field.options != {}
                assert field.options['geo_type'] == 'name'
                assert 'admin_level' in field.options

        if not geofield:
            return

        sheet = Sheet.objects.last()
        assert 'processed_values' in sheet.data
        processed = sheet.data['processed_values']

        fid = str(geofield.id)
        assert fid in processed
        kathmandu_geo = GeoArea.objects.filter(code='KAT')[0]

        for val in processed[fid]:
            assert val == kathmandu_geo.id

    def test_auto_detection_geo_type_code(self):
        """
        Testing geo type code
        """
        book = self.initialize_data_and_basic_test(geo_data_type_code)
        # now auto detect
        auto_detect_and_update_fields(book)
        sheets = book.sheet_set.all()
        for sheet in sheets:
            # TODO: check processed values
            pass

        geofield = None
        # now validate auto detected fields
        for field in Field.objects.all():
            if field.title == 'place':
                geofield = field
                assert field.type == Field.GEO,\
                    'place is geo: more than 80% rows are of geo type'
                assert field.options != {}
                assert field.options['geo_type'] == 'code'

        if not geofield:
            return

        sheet = Sheet.objects.last()
        assert 'processed_values' in sheet.data
        processed = sheet.data['processed_values']

        fid = str(geofield.id)
        assert fid in processed
        kathmandu_geo = GeoArea.objects.filter(code='KAT')[0]

        for i, val in enumerate(processed[fid]):
            assert val == kathmandu_geo.id

    def test_sheet_data_change_on_datefield_change_to_string(self):
        """
        Update value type in sheet data rows when field type changed

        This basically tries to cast row values to field type. In this case,
        all values should be cast because we're casting to string
        """
        book = self.initialize_data_and_basic_test(consistent_csv_data)
        auto_detect_and_update_fields(book)

        sheet = book.sheet_set.all()[0]

        # Now update date_field to string
        field = Field.objects.get(
            sheet=sheet,
            type=Field.DATETIME
        )
        field.type = Field.STRING
        field.save()

        # Get sheet again, which should be updated
        new_sheet = Sheet.objects.get(id=sheet.id)

        invalids = new_sheet.data['invalid_values']
        assert invalids[str(field.id)] == [], \
            "Conversion to string should give no invalids"

    def test_sheet_data_change_on_string_change_to_geo(self):
        """
        Update value type in sheet data rows when field type changed

        This basically tries to cast row values to field type.
        """
        book = self.initialize_data_and_basic_test(consistent_csv_data)
        auto_detect_and_update_fields(book)

        sheet = book.sheet_set.all()[0]

        # We first cast geo field to string because initially it will be auto
        # detected as geo
        field = Field.objects.get(
            sheet=sheet,
            type=Field.GEO
        )
        fid = str(field.id)
        field.type = Field.STRING
        field.save()

        # Get sheet again, which should be updated
        new_sheet = Sheet.objects.get(id=sheet.id)

        invalids = new_sheet.data['invalid_values']
        assert invalids[str(field.id)] == [], \
            "Conversion to string should give no invalids"

        # Now change type to Geo
        field.type = Field.GEO
        field.save()

        # Get sheet again, which should be updated
        brand_new_sheet = Sheet.objects.get(id=sheet.id)

        invalids = brand_new_sheet.data['invalid_values'][fid]
        # NOTE: look at consistent_csv_data value
        assert invalids == [6, 8]

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

        # check structure of data in sheet
        for sheet in book.sheet_set.all():
            data = sheet.data
            assert 'columns' in data
            columns = data['columns']
            assert isinstance(columns, dict)

            # check col sizes, whichs should be same
            colsizes = [len(v) for k, v in columns.items()]
            if not colsizes:
                continue
            size = colsizes[0]
            assert reduce(lambda a, x: x == size and a, colsizes, True), \
                "All columns should have same size"

            for k, v in columns.items():
                assert isinstance(v, list)

            # Check for invalid_values
            if 'invalid_values' in data:
                invalids = data['invalid_values']
                assert isinstance(invalids, dict)
                for k, v in invalids.items():
                    assert k in columns
                    assert isinstance(v, list)
                    for x in v:
                        assert isinstance(x, int)
                        assert x >= 0 and x < size, \
                            "Since invalid_values store indices, should be within range"  # noqa

            # Check for empty_values
            if 'empty_values' in data:
                invalids = data['empty_values']
                assert isinstance(invalids, dict)
                for k, v in invalids.items():
                    assert k in columns
                    assert isinstance(v, list)
                    for x in v:
                        assert isinstance(x, int)
                        assert x >= 0 and x < size, \
                            "Since empty_values stores indices, should be within range"  # noqa
        return book

    def tearDown(self):
        """Remove temp files"""
        for file in self.files:
            os.remove(file)
