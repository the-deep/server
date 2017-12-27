from .formats.xlsx import WorkBook, RowsBuilder
from .common import format_date


class EntriesExporter:
    def __init__(self):
        self.wb = WorkBook()

        self.split = self.wb.get_active_sheet\
            .set_title('Split Entries')
        self.group = self.wb.create_sheet('Grouped Entries')

        self.titles = [
            'Date of Lead Publication',
            'Imported By',
            'Date Imported',
            'Lead Title',
            'Source',
            'Excerpt',
        ]
        self.info_date = None

    def load_exportables(self, exportables, regions=None):
        exportables = exportables.filter(
            data__isnull=False,
        )

        information_date_index = 1
        for exportable in exportables:
            data = exportable.data
            export_type = data.get('type')

            if export_type == 'information-date':
                self.titles.insert(
                    information_date_index,
                    data.get('title'),
                )
                information_date_index += 1

            elif export_type == 'geo' and regions:
                for region in regions:
                    admin_levels = region.adminlevel_set.all()
                    for admin_level in admin_levels:
                        self.titles.append(admin_level.title)

            else:
                self.titles.append(data.get('title'))

        self.exportables = exportables
        self.regions = regions

    def add_entries(self, entries):
        for entry in entries:
            rows = RowsBuilder(self.split, self.group)
            rows.add_value(format_date(entry.lead.published_on))

            # TODO Check for information dates

            rows.add_value_list([
                entry.created_by,
                format_date(entry.created_at.date()),
                entry.lead.title,
                entry.lead.source,
                entry.excerpt,
            ])

            rows.apply()
