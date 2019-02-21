import io
import csv
from itertools import chain
from ..models import Sheet, Field

from utils.common import LogTime


@LogTime()
def extract(book):
    options = book.options if book.options else {}
    Sheet.objects.filter(book=book).delete()  # Delete all previous sheets
    with book.get_file() as csv_file:
        sheet = Sheet.objects.create(
            title=book.title,
            book=book,
        )
        reader = csv.reader(
            io.StringIO(csv_file.read().decode('utf-8')),
            delimiter=options.get('delimiter', ','),
            quotechar=options.get('quotechar', '"'),
            skipinitialspace=True,
        )

        no_headers = options.get('no_headers', False)

        fields = []
        ordering = 1

        first_row = list(next(reader))  # first row might be used later as data

        for header in first_row:
            fields.append(
                Field(
                    title=(header if not no_headers
                           else 'Column ' + str(ordering)),
                    sheet=sheet,
                    ordering=ordering,
                )
            )
            ordering += 1
        Field.objects.bulk_create(fields)

        # Create a new iterator with already extracted first row if no_headers
        rows_iterator = chain(iter([first_row]), reader)\
            if no_headers else reader

        fields_data = {}
        for _row in rows_iterator:
            try:
                for index, field in enumerate(fields):
                    field_data = fields_data.get(field.id, [])
                    field_data.append({
                        'value': _row[index],
                        'invalid': False,
                        'empty': False,
                    })
                    fields_data[field.id] = field_data
            except Exception:
                pass

        for field in sheet.field_set.all():
            field.data = fields_data.get(field.id, [])
            field.save()
