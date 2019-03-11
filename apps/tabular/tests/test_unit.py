import os
from autofixture.base import AutoFixture
from tempfile import NamedTemporaryFile

from django.conf import settings

from deep.tests import TestCase

from gallery.models import File
from geo.models import GeoArea, Region

from project.models import Project

from tabular.tasks import auto_detect_and_update_fields
from tabular.extractor import csv
from tabular.models import Book, Field, Sheet
from tabular.utils import (
    parse_comma_separated,
    parse_dot_separated,
    parse_space_separated,
    auto_detect_datetime,
)

consistent_csv_data = '''id,age,name,date,place
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,Kathmandu
1,10,john,2018 october 28,banana
1,10,john,2018 october 28,
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
abc,30,doe,10 Nevem 2018,'''


def check_invalid(index, data):
    assert 'invalid' in data[index]
    assert data[index]['invalid'] is True


def check_empty(index, data):
    assert 'empty' in data[index]
    assert data[index]['empty'] is True


class TestTabularExtraction(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = []

    def setUp(self):
        super().setUp()
        Book.objects.all().delete()
        # geo_choices = ChoicesGenerator(values=areas)
        # NOTE: Using choices created random values, and thus error occured
        self.project = self.create(Project)
        AutoFixture(
            GeoArea,
            field_values={
                'title': 'Kathmandu',
                'code': 'KAT'
            },
            generate_fk=True
        ).create(1)
        self.region = Region.objects.first()
        self.project.regions.add(self.region)
        self.project.save()

    def test_auto_detection_consistent(self):
        """
        Testing rows having consistent values
        """
        book = self.initialize_data_and_basic_test(consistent_csv_data)
        # now auto detect
        auto_detect_and_update_fields(book)

        # Check for sheet invalid/empty values
        sheet = Sheet.objects.last()

        # now validate auto detected fields
        for field in Field.objects.filter(sheet=sheet):
            assert len(field.data) == 10

            if field.title == 'id':
                assert field.type == Field.NUMBER, 'id is number'
                assert 'separator' in field.options
                assert field.options['separator'] == 'none'
                self.validate_number_field(field.data)
                # Check invalid values
                check_invalid(8, field.data)
                check_invalid(9, field.data)
            elif field.title == 'age':
                assert field.type == Field.NUMBER, 'age is number'
                assert 'separator' in field.options
                assert field.options['separator'] == 'none'
                self.validate_number_field(field.data)
            elif field.title == 'name':
                assert field.type == Field.STRING, 'name is string'
            elif field.title == 'date':
                assert field.type == Field.DATETIME, 'date is datetime'
                assert field.options is not None
                assert 'date_format' in field.options
                for datum in field.data:
                    assert datum.get('invalid') is not None or \
                        datum.get('empty') is not None or \
                        'processed_value' in datum
                check_invalid(9, field.data)
            elif field.title == 'place':
                assert field.type == Field.GEO, 'place is geo'
                assert field.options is not None
                assert 'regions' in field.options
                assert 'admin_level' in field.options
                for x in field.options['regions']:
                    assert 'id' in x
                    assert 'title' in x

                check_invalid(6, field.data)
                check_empty(7, field.data)
                check_invalid(8, field.data)

    def test_auto_detection_inconsistent(self):
        """
        Testing rows having inconsistent values
        """
        book = self.initialize_data_and_basic_test(inconsistent_csv_data)
        # now auto detect
        auto_detect_and_update_fields(book)

        sheet = Sheet.objects.last()

        # now validate auto detected fields
        for field in Field.objects.filter(sheet=sheet):
            for v in field.data:
                assert isinstance(v, dict)

            if field.title == 'id':
                assert field.type == Field.STRING,\
                    'id is string as it is inconsistent'
                # Verify that being string, no value is invalid
                for v in field.data:
                    assert not v.get('invalid'),\
                        "Since string, shouldn't be invalid"
            elif field.title == 'age':
                assert field.type == Field.NUMBER, 'age is number'
                assert 'separator' in field.options
                assert field.options['separator'] == 'none'
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
                assert 'regions' in field.options
                assert 'admin_level' in field.options
                for x in field.options['regions']:
                    assert 'id' in x
                    assert 'title' in x
                assert 'geo_type' in field.options
                assert field.options['geo_type'] == 'name'

        if not geofield:
            return

        kathmandu_geo = GeoArea.objects.filter(code='KAT')[0]

        for v in geofield.data:
            assert v.get('invalid') or v.get('empty') or 'processed_value' in v
            assert 'value' in v
            assert v.get('empty') \
                or v.get('invalid') \
                or v['processed_value'] == kathmandu_geo.id

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
                assert 'regions' in field.options
                assert 'admin_level' in field.options
                for x in field.options['regions']:
                    assert 'id' in x
                    assert 'title' in x
                assert 'geo_type' in field.options
                assert field.options['geo_type'] == 'code'

        if not geofield:
            return

        kathmandu_geo = GeoArea.objects.filter(code='KAT')[0]

        for v in geofield.data:
            assert v.get('invalid') or v.get('empty') or 'processed_value' in v
            assert 'value' in v
            assert v.get('empty') \
                or v.get('invalid') \
                or v['processed_value'] == kathmandu_geo.id

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

        # no vlaue should be invalid
        for v in field.data:
            print(field.type, v['value'])
            assert not v.get('invalid', None)

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
        options = field.options

        fid = str(field.id)
        field.type = Field.STRING
        field.options = {}
        field.save()

        # no value should be invalid
        for v in field.data:
            assert not v.get('invalid')
        # Now change type to Geo
        field.type = Field.GEO

        # Try removing region, and check if it's automatically added from admin
        # level
        options.pop('region', {})
        field.options = {
            **options,
        }
        field.save()

        kat_geo = GeoArea.objects.filter(code='KAT')[0]

        # Check if field has region
        field = Field.objects.get(id=fid)
        assert 'regions' in field.options
        regions = field.options['regions']
        for x in regions:
            assert 'id' in x
            assert 'title' in x
        assert field.options['admin_level'] == kat_geo.admin_level.level
        assert regions[0]['id'] == kat_geo.admin_level.region.id

        # Get sheet again, which should be updated

        check_invalid(6, field.data)
        check_empty(7, field.data)
        check_invalid(8, field.data)

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
                'file': csvfile,
                'project': self.project,
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
            fields = sheet.field_set.all()
            size = len(fields[0].data)
            assert all([len(x.data) == size for x in fields]), \
                "All columns should have same size"

            for field in fields:
                v = field.data
                assert isinstance(v, list)
                for x in v:
                    assert 'value' in x
                    assert 'empty' in x
                    assert isinstance(x['empty'], bool)
                    assert 'invalid' in x
                    assert isinstance(x['invalid'], bool)
        return book

    def validate_number_field(self, items):
        for i, item in enumerate(items):
            assert 'value' in item
            assert item.get('invalid') \
                or item.get('empty') \
                or ('processed_value' in item)
            assert not item.get('processed_value') \
                or isinstance(item['processed_value'], int)\
                or isinstance(item['processed_value'], float)

    def tearDown(self):
        """Remove temp files"""
        for file in self.files:
            os.remove(file)


def test_comma_separated_numbers():
    assert parse_comma_separated('1') == (1.0, 'comma')
    assert parse_comma_separated('12') == (12.0, 'comma')
    assert parse_comma_separated('100') == (100.0, 'comma')
    assert parse_comma_separated('1,200') == (1200.0, 'comma')
    assert parse_comma_separated('11,200') == (11200.0, 'comma')
    assert parse_comma_separated('111,200') == (111200.0, 'comma')
    assert parse_comma_separated('5,111,200') == (5111200.0, 'comma')
    assert parse_comma_separated('54,111,200') == (54111200.0, 'comma')
    assert parse_comma_separated('543,111,200') == (543111200.0, 'comma')
    assert parse_comma_separated('543111,200') is None
    assert parse_comma_separated('1,200.35') == (1200.35, 'comma')
    assert parse_comma_separated('1,200.35.3') is None
    assert parse_comma_separated('') is None
    assert parse_comma_separated(None) is None
    assert parse_comma_separated('abc,123') is None
    assert parse_comma_separated('123,abc,123') is None


def test_dot_separated_numbers():
    assert parse_dot_separated('1') == (1.0, 'dot')
    assert parse_dot_separated('12') == (12.0, 'dot')
    assert parse_dot_separated('100') == (100.0, 'dot')
    assert parse_dot_separated('1.200') == (1200.0, 'dot')
    assert parse_dot_separated('11.200') == (11200.0, 'dot')
    assert parse_dot_separated('111.200') == (111200.0, 'dot')
    assert parse_dot_separated('5.111.200') == (5111200.0, 'dot')
    assert parse_dot_separated('54.111.200') == (54111200.0, 'dot')
    assert parse_dot_separated('543.111.200') == (543111200.0, 'dot')
    assert parse_dot_separated('543111.200') is None
    assert parse_dot_separated('1.200,35') == (1200.35, 'dot')
    assert parse_dot_separated('1.200,35,3') is None
    assert parse_dot_separated('') is None
    assert parse_dot_separated(None) is None
    assert parse_dot_separated('abc.123') is None
    assert parse_dot_separated('123.abc.123') is None


def test_space_separated_numbers():
    assert parse_space_separated('1') == (1.0, 'space')
    assert parse_space_separated('12') == (12.0, 'space')
    assert parse_space_separated('100') == (100.0, 'space')
    assert parse_space_separated('1 200') == (1200.0, 'space')
    assert parse_space_separated('11 200') == (11200.0, 'space')
    assert parse_space_separated('111 200') == (111200.0, 'space')
    assert parse_space_separated('5 111 200') == (5111200.0, 'space')
    assert parse_space_separated('54 111 200') == (54111200.0, 'space')
    assert parse_space_separated('543 111 200') == (543111200.0, 'space')
    assert parse_space_separated('543111 200') is None
    assert parse_space_separated('1 200.35') == (1200.35, 'space')
    assert parse_space_separated('1 200.35.3') is None
    assert parse_space_separated('') is None
    assert parse_space_separated(None) is None
    assert parse_space_separated('abc 123') is None
    assert parse_space_separated('123 abc 123') is None


def test_parse_date():
    assert auto_detect_datetime('2019-03-15') is not None
    assert auto_detect_datetime('2019-Dec-15') is not None
    assert auto_detect_datetime('2019-Oct-15') is not None

    assert auto_detect_datetime('2019-03-15') is not None
    assert auto_detect_datetime('2019-Dec-15') is not None
    assert auto_detect_datetime('2019-Oct-15') is not None

    assert auto_detect_datetime('2019-December-15') is not None
    assert auto_detect_datetime('2019 October 15') is not None
