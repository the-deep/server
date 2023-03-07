import csv


class ExportColumn:
    TITLE = 'Title'
    PILLAR = 'Pillar'
    SUB_PILLAR = 'Sub pillar'
    COLUMN_2D = '2D column'
    SUB_COLUMN_2D = '2D sub column'


AF_EXPORT_COLUMNS = [
    ExportColumn.TITLE,
    ExportColumn.PILLAR,
    ExportColumn.SUB_PILLAR,
    ExportColumn.COLUMN_2D,
    ExportColumn.SUB_COLUMN_2D,
]


def export_af_to_csv(af, file):
    """
    Only extracts this widgets
    - matrix1dWidget
    - matrix2dWidget
    """
    writer = csv.DictWriter(file, fieldnames=AF_EXPORT_COLUMNS)
    writer.writeheader()

    for widget in af.widget_set.order_by('widget_id'):
        w_type = widget.widget_id
        w_title = widget.title

        widget_prop = widget.properties or {}
        if w_type == 'matrix1dWidget':
            for row in widget_prop['rows']:
                for cell in row['cells']:
                    writer.writerow({
                        ExportColumn.TITLE: w_title,
                        ExportColumn.PILLAR: row['label'],
                        ExportColumn.SUB_PILLAR: cell['label'],
                    })

        elif w_type == 'matrix2dWidget':
            for row in widget_prop['rows']:
                for sub_row in row['subRows']:
                    for column in widget_prop['columns']:
                        for sub_column in column['subColumns']:
                            writer.writerow({
                                ExportColumn.TITLE: w_title,
                                ExportColumn.PILLAR: row['label'],
                                ExportColumn.SUB_PILLAR: sub_row['label'],
                                ExportColumn.COLUMN_2D: column['label'],
                                ExportColumn.SUB_COLUMN_2D: sub_column['label'],
                            })
