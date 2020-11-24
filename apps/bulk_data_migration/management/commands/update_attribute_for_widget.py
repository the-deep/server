from datetime import datetime, timedelta
import os

from django.core.management.base import BaseCommand
from django.db.models import Q, Max, Min, OuterRef, Subquery, DateTimeField

from entry.models import Attribute
from entry.utils import update_entry_attribute
from entry.widgets.store import widget_store
from entry.widgets import conditional_widget
from lead.models import Lead
from project.models import Project

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

    def handle(self, *args, **options):
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
            for attr in qs.filter(widget__widget_id=widget):
                update_entry_attribute(attr)
            for attr in qs.filter(widget__widget_id=conditional_widget.WIDGET_ID):
                if widget in [each['widget']['widget_id'] for each in attr.widget.properties['data']['widgets']]:
                    update_entry_attribute(attr)
        else:
            for attr in qs:
                update_entry_attribute(attr)
