from datetime import datetime, timedelta
import time

from django.core.management.base import BaseCommand
from django.db.models import (
    Q,
    Max,
    OuterRef,
    Subquery,
    DateTimeField,
    Exists
)

from entry.models import Attribute, ExportData
from entry.utils import update_entry_attribute
from entry.widgets.store import widget_store
from entry.widgets import conditional_widget
from lead.models import Lead

HIGH = 3
MEDIUM = 2
LOW = 1


class Command(BaseCommand):
    help = 'Update attributes to export widget'

    def add_arguments(self, parser):
        parser.add_argument(
            '--priority',
            type=int,
            help='Priority based on last activity of leads (high: >{}, medium: {}, low: <{})'.format(
                HIGH, MEDIUM, LOW
            ),
        )
        parser.add_argument(
            '--project',
            type=int,
            help='Specific project export data migration',
        )
        parser.add_argument(
            '--widget',
            type=str,
            help='Specific widget export data migration',
        )

    def update_attributes(self, widget, qs):
        if not qs.exists():
            return
        if widget == conditional_widget.WIDGET_ID:
            # conditional widget is handled within each overview widget
            return
        curr_data_version = getattr(widget_store[widget], 'DATA_VERSION', None)
        to_be_changed_export_data_exists = Exists(
            ExportData.objects.filter(
                exportable__widget_key=OuterRef('widget__key'),
                entry_id=OuterRef('entry')
            ).filter(
                ~Q(data__has_key='common') |
                ~Q(data__common__has_key='version') |
                (
                    Q(data__has_key='common') &
                    Q(data__common__has_key='version') &
                    ~Q(data__common__version=curr_data_version)
                )
            )
        )
        count = 0
        for attr in qs.filter(widget__widget_id=widget).annotate(
            export_data_exists=to_be_changed_export_data_exists
        ).filter(export_data_exists=True):
            count += 1
            update_entry_attribute(attr)

        to_be_changed_export_data_conditional_exists = Exists(
            ExportData.objects.filter(
                exportable__widget_key=OuterRef('widget__key'),
                entry_id=OuterRef('entry'),
            ).filter(
                ~Q(data__has_key='common') |
                # ~Q(data__common__has_key=widget) |
                (
                    Q(data__has_key='common') &
                    Q(data__common__has_key=widget) &
                    ~Q(**{f'data__common__{widget}': curr_data_version})
                )
            )
        )
        count2 = 0
        for attr in qs.filter(widget__widget_id=conditional_widget.WIDGET_ID).annotate(
            export_data_exists=to_be_changed_export_data_conditional_exists
        ).filter(export_data_exists=True):
            count2 += 1
            update_entry_attribute(attr)

        print(f'Updated {count} overview and {count2} conditional widgets for {widget}.')

    def handle(self, *args, **options):
        old = time.time()
        qs = Attribute.objects.all()
        if options.get('project'):
            qs = qs.filter(entry__project=options['project'])
        elif options.get('priority'):
            today = datetime.today()
            priority = options['priority']
            last_30_days_ago = today - timedelta(days=30)
            last_60_days_ago = today - timedelta(days=60)
            qs = qs.annotate(
                last_lead_added=Subquery(Lead.objects.filter(
                    project=OuterRef('entry__project_id')
                ).order_by().values('project').annotate(max=Max('created_at')).values('max')[:1],
                    output_field=DateTimeField())
            )
            if priority >= HIGH:
                qs = qs.filter(last_lead_added__gte=last_30_days_ago)
            elif priority == MEDIUM:
                qs = qs.filter(last_lead_added__lt=last_30_days_ago,
                               last_lead_added__gte=last_60_days_ago)
            else:
                qs = qs.filter(last_lead_added__lt=last_60_days_ago)

        if options.get('widget') in widget_store.keys():
            widget = options['widget']
            qs = qs.filter(Q(widget__widget_id=widget) | Q(widget__widget_id=conditional_widget.WIDGET_ID))
            self.update_attributes(widget, qs)
        else:
            for widget in widget_store.keys():
                self.update_attributes(widget, qs.filter(
                    Q(widget__widget_id=widget) | Q(widget__widget_id=conditional_widget.WIDGET_ID)
                ))
        print(f'Checked on {qs.count()} attributes.')
        print(f'It took {time.time() - old} seconds.')
