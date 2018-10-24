import io
import csv
from ..models import Sheet, Field


def extract(book):
    options = book.options if book.options else {}
    sheet = Sheet.objects.create(
        title=book.title,
        book=book,
    )
    with book.file.file as csv_file:
        csv_file.open()
        reader = csv.reader(
            io.StringIO(csv_file.read().decode('utf-8')),
            delimiter=options.get('delimiter', ','),
            quotechar=options.get('quotechar', '"'),
        )

        fields = []
        for header in next(reader):
            fields.append(
                Field(
                    label=header,
                    sheet=sheet,
                )
            )
        Field.objects.bulk_create(fields)

        rows = []
        for _row in reader:
            row = {}
            for index, field in enumerate(fields):
                row[str(field.pk)] = _row[index]
            rows.append(row)
        sheet.data = rows
        sheet.save()
