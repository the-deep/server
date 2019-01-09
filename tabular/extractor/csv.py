import io
import csv
from itertools import chain
from utils.common import random_key
from ..models import Sheet, Field


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

        rows = []
        for _row in rows_iterator:
            row = {}
            try:
                for index, field in enumerate(fields):
                    row[str(field.pk)] = {
                        'value': _row[index],
                        'type': Field.STRING
                    }
                row['key'] = random_key()
                rows.append(row)
            except Exception:
                pass
        sheet.data = rows
        sheet.save()
