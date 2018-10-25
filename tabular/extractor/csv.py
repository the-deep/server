import io
import csv
from utils.common import random_key
from ..models import Sheet, Field


def extract(book):
    options = book.options if book.options else {}
    sheet = Sheet.objects.filter(book=book).delete()
    with book.get_file() as csv_file:
        sheet = Sheet.objects.create(
            title=book.title,
            book=book,
        )
        reader = csv.reader(
            io.StringIO(csv_file.read().decode('utf-8')),
            delimiter=options.get('delimiter', ','),
            quotechar=options.get('quotechar', '"'),
        )

        fields = []
        for header in next(reader):
            fields.append(
                Field(
                    title=header,
                    sheet=sheet,
                )
            )
        Field.objects.bulk_create(fields)

        rows = []
        for _row in reader:
            row = {}
            try:
                for index, field in enumerate(fields):
                    row[str(field.pk)] = _row[index]
                row['key'] = random_key()
                rows.append(row)
            except Exception:
                pass
        sheet.data = rows
        sheet.save()
