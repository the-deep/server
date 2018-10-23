import io
import csv
from ..models import Sheet, Field, Cell


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

        cell = []
        for row in reader:
            for index, field in enumerate(fields):
                cell.append(
                    Cell(
                        field=field,
                        value=row[index],
                    ))
        Cell.objects.bulk_create(cell)
