from django.test import TestCase
from export.formats.xlsx import RowsBuilder


class RowsBuilderTest(TestCase):
    def test_rows(self):
        builder = RowsBuilder()\
            .add_value('Hello')\
            .add_value_list(['My', 'Name'])\
            .add_rows_of_values(['Is', 'Not', 'Jon'])\
            .add_rows_of_values(['1', '2'])\
            .add_rows_of_value_lists([['3', '4'], ['5', '6']])

        result = [
            ['Hello', 'My', 'Name', 'Is', '1', '3', '4'],
            ['Hello', 'My', 'Name', 'Not', '1', '3', '4'],
            ['Hello', 'My', 'Name', 'Jon', '1', '3', '4'],
            ['Hello', 'My', 'Name', 'Is', '2', '3', '4'],
            ['Hello', 'My', 'Name', 'Not', '2', '3', '4'],
            ['Hello', 'My', 'Name', 'Jon', '2', '3', '4'],
            ['Hello', 'My', 'Name', 'Is', '1', '5', '6'],
            ['Hello', 'My', 'Name', 'Not', '1', '5', '6'],
            ['Hello', 'My', 'Name', 'Jon', '1', '5', '6'],
            ['Hello', 'My', 'Name', 'Is', '2', '5', '6'],
            ['Hello', 'My', 'Name', 'Not', '2', '5', '6'],
            ['Hello', 'My', 'Name', 'Jon', '2', '5', '6'],
        ]

        group_result = [
            'Hello', 'My', 'Name', 'Is, Not, Jon', '1, 2', '3, 5', '4, 6'
        ]

        self.assertEqual(result, builder.rows)
        self.assertEqual(group_result, builder.group_rows)
