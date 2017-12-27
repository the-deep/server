from .formats.xlsx import WorkBook, RowsBuilder
from .common import format_date

from entry.models import ExportData


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

        # information_date_index = 1
        for exportable in exportables:
            data = exportable.data
            export_type = data.get('type')

            # if export_type == 'information-date':
            #     self.titles.insert(
            #         information_date_index,
            #         data.get('title'),
            #     )
            #     information_date_index += 1

            if export_type == 'geo' and regions:
                for region in regions:
                    admin_levels = region.adminlevel_set.all()
                    for admin_level in admin_levels:
                        self.titles.append(admin_level.title)

            elif export_type == 'multiple':
                self.titles.extend(data.get('titles'))

            elif data.get('title'):
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

            for exportable in self.exportables:
                data = exportable.data
                export_data = ExportData.objects.filter(
                    exportable=exportable,
                    entry=entry,
                ).first()
                export_data = export_data and export_data.data
                export_type = data.get('type')

                if export_type == 'multiple':
                    if export_data:
                        if export_data.get('type') == 'lists':
                            rows.add_rows_of_value_lists(
                                export_data.get('values')
                            )
                        else:
                            rows.add_value_list(
                                export_data.get('values')
                            )
                    else:
                        rows.add_value('' * len(data.get('titles')))

                elif export_type == 'geo' and self.regions:
                    geo_data = {}
                    if export_data:
                        geo_data = export_data.geo_data

                    for region in self.regions:
                        region_data = geo_data.get(region.code, {})
                        admin_levels = region.adminlevel_set.all()

                        for admin_level in admin_levels:
                            al_data = region_data.get(admin_level.level, [''])
                            rows.add_rows_of_values(al_data)

                else:
                    if export_data:
                        if export_data.get('type') == 'list':
                            rows.add_rows_of_values(export_data.get('value'))
                        else:
                            rows.add_value(export_data.get('value'))

            rows.apply()
